__author__ = "Simon Nilsson"

import os.path
import pandas as pd
import numpy as np
from numba import jit, prange
from numba.typed import List
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.sparse import csgraph
from simba.unsupervised.enums import Unsupervised, Clustering
from simba.mixins.unsupervised_mixin import UnsupervisedMixin
from simba.mixins.config_reader import ConfigReader
from simba.utils.printing import stdout_success, stdout_warning, SimbaTimer
from simba.utils.checks import check_if_dir_exists, check_file_exist_and_readable



CLUSTERER_NAME = 'CLUSTERER_NAME'
CLUSTER_COUNT = 'CLUSTER_COUNT'
EMBEDDER_NAME = 'EMBEDDER_NAME'
DBCV = 'DBCV'


class DBCVCalculator(UnsupervisedMixin, ConfigReader):
    """
    Density-based Cluster Validation (DBCV).

    .. note::
       Jitted version of `DBCSV <https://github.com/christopherjenness/DBCV>`__.
       Faster runtime by replacing meth:`scipy.spatial.distance.cdist` in original DBCSV with LLVM as discussed
       `HERE <https://github.com/numba/numba-scipy/issues/38>`__.

    :param str embedders_path: Directory holding dimensionality reduction models in pickle format.
    :param str clusterers_path: Directory holding cluster models in pickle format.

    References
    ----------
    .. [1] Moulavi et al, Density-Based Clustering Validation, `SIAM 2014`, https://doi.org/10.1137/1.9781611973440.96

    Examples
    -----
    >>> dbcv_calculator = DBCVCalculator(clusterers_path='unsupervised/cluster_models', config_path='my_simba_config')
    >>> results = dbcv_calculator.run()
    """

    def __init__(self,
                 config_path: str,
                 data_path: str):

        ConfigReader.__init__(self, config_path=config_path)
        UnsupervisedMixin.__init__(self)
        if os.path.isdir(data_path):
            check_if_dir_exists(in_dir=data_path)
            self.data = self.read_pickle(data_path=data_path)
        else:
            check_file_exist_and_readable(file_path=data_path)
            self.data = {0: self.read_pickle(data_path=data_path)}
        self.save_path = os.path.join(self.logs_path, f'DBCV_{self.datetime}.xlsx')
        with pd.ExcelWriter(self.save_path, mode='w') as writer:
            pd.DataFrame().to_excel(writer, sheet_name=' ', index=True)

    def run(self):
        print(f'Analyzing DBCV for {len(self.data.keys())} clusterers...')
        self.results = {}
        for k, v in self.data.items():
            model_timer = SimbaTimer(start=True)
            self.results[k], dbcv_results = {}, 'nan'
            self.results[k][CLUSTERER_NAME] = v[Clustering.CLUSTER_MODEL.value][Unsupervised.HASHED_NAME.value]
            self.results[k][EMBEDDER_NAME] = v[Unsupervised.DR_MODEL.value][Unsupervised.HASHED_NAME.value]
            print(f"Performing DBCV for cluster model {self.results[k][CLUSTERER_NAME]}...")
            cluster_lbls = v[Clustering.CLUSTER_MODEL.value][Unsupervised.MODEL.value].labels_
            x = v[Unsupervised.DR_MODEL.value][Unsupervised.MODEL.value].embedding_
            self.results[k] = {**self.results[k], **v[Clustering.CLUSTER_MODEL.value][Unsupervised.PARAMETERS.value], **v[Unsupervised.DR_MODEL.value][Unsupervised.PARAMETERS.value]}
            cluster_cnt = self.get_cluster_cnt(data=cluster_lbls, clusterer_name=v[Clustering.CLUSTER_MODEL.value][Unsupervised.HASHED_NAME.value], minimum_clusters=1)

            if cluster_cnt > 1:
                dbcv_results = self.DBCV(x, cluster_lbls)
            else:
                stdout_warning(msg=f'No DBCV calculated for clusterer {self.results[k][CLUSTERER_NAME]}: Less than two clusters identified.')
            self.results[k] = {**self.results[k], **{DBCV: dbcv_results}, **{CLUSTER_COUNT: cluster_cnt}}
            model_timer.stop_timer()
            stdout_success(msg=f"DBCV complete for model {self.results[k][CLUSTERER_NAME]}", elapsed_time=model_timer.elapsed_time_str)
        self.__save_results()
        self.timer.stop_timer()
        stdout_success(msg=f"ALL DBCV calculations complete and saved in {self.save_path}", elapsed_time=self.timer.elapsed_time_str)

    def __save_results(self):
        for k, v in self.results.items():
            df = pd.DataFrame.from_dict(v, orient='index', columns=['VALUE'])
            with pd.ExcelWriter(self.save_path, mode='a') as writer:
                df.to_excel(writer, sheet_name=v[CLUSTERER_NAME], index=True)

    def DBCV(self, X, labels):
        """
        Parameters
        ----------
        X : array with shape len(observations) x len(dimentionality reduced dimensions)
        labels : 1D array with cluster labels

        Returns
        -------
        DBCV_validity_index: DBCV cluster validity score

        """

        neighbours_w_labels, ordered_labels = self._mutual_reach_dist_graph(X, labels)
        graph = self.calculate_dists(X, neighbours_w_labels)
        mst = self._mutual_reach_dist_MST(graph)
        return self._clustering_validity_index(mst, ordered_labels)

    @staticmethod
    @jit(nopython=True)
    def _mutual_reach_dist_graph(X, labels):
        """
        Parameters
        ----------
        X :  array with shape len(observations) x len(dimensionality reduced dimensions)
        labels : 1D array with cluster labels

        Returns
        -------
        arrays_by_cluster: 3D array in numba ListType, of shape len(number of clusters) x len(cluster_members) x len(dimensionality reduced dimensions)
        ordered_labels:  numba ListType of labels in the order of arrays_by_cluster
        """
        unique_cluster_labels = np.unique(labels)
        arrays_by_cluster = List()
        ordered_labels = List()

        def _get_label_members(X, labels, cluster_label):
            indices = np.where(labels == cluster_label)[0]
            members = X[indices]
            return members

        for cluster_label_idx in prange(unique_cluster_labels.shape[0]):
            cluster_label = unique_cluster_labels[cluster_label_idx]
            members = _get_label_members(X, labels, cluster_label)
            ordered_labels.append([cluster_label] * len(members))
            arrays_by_cluster.append([members])

        ordered_labels = [i for s in ordered_labels for i in s]
        return arrays_by_cluster, ordered_labels

    @staticmethod
    @jit(nopython=True, fastmath=True)
    def calculate_dists(X, arrays_by_cluster):
        """
        Parameters
        ----------
        arrays_by_cluster: 3D array in numba ListType, of shape len(number of clusters) x len(cluster_members) x len(dimentionality reduced dimensions

        Returns
        -------
        graph: Graph of all pair-wise mutual reachability distances between points.

        """

        cluster_n = len(arrays_by_cluster)
        graph = np.empty((X.shape[0], X.shape[0]), X.dtype)
        graph_row_counter = 0

        for cluster_a in range(cluster_n):
            A = arrays_by_cluster[cluster_a][0]
            for a in prange(A.shape[0]):
                Ci = np.empty((A.shape[0]), A.dtype)
                init_val_arr = np.zeros(1, A.dtype)
                init_val = init_val_arr[0]
                for j in range(A.shape[0]):
                    acc = init_val
                    for k in range(A.shape[1]):
                        acc += (A[a, k] - A[j, k]) ** 2
                    Ci[j] = np.sqrt(acc)

                indices = np.where(Ci != 0)
                Ci = Ci[indices]

                numerator = ((1 / Ci) ** A.shape[1]).sum()
                core_dist_i = (numerator / (A.shape[0] - 1)) ** (-1 / A.shape[1])
                graph_row = np.zeros((0))

                for array_cnt in range(len(arrays_by_cluster)):
                    B = arrays_by_cluster[array_cnt][0]
                    for b in prange(B.shape[0]):
                        Cii = np.empty((B.shape[0]), B.dtype)
                        init_val_arr = np.zeros(1, B.dtype)
                        init_val = init_val_arr[0]
                        for j in range(B.shape[0]):
                            acc = init_val
                            for k in range(B.shape[1]):
                                acc += (B[b, k] - B[j, k]) ** 2
                            Cii[j] = np.sqrt(acc)
                        indices_ii = np.where(Cii != 0)
                        Cii = Cii[indices_ii]

                        numerator = ((1 / Cii) ** B.shape[1]).sum()
                        core_dist_j = (numerator / (B.shape[0] - 1)) ** (-1 / B.shape[1])
                        dist = np.linalg.norm(A[a] - B[b])
                        mutual_reachability = np.max(np.array([core_dist_i, core_dist_j, dist]))
                        graph_row = np.append(graph_row, mutual_reachability)

                graph[graph_row_counter] = graph_row
                graph_row_counter += 1

        return graph

    def _mutual_reach_dist_MST(self, dist_tree):
        """
        Parameters
        dist_tree : array of dimensions len(observations) x len(observations


        Returns
        -------
        minimum_spanning_tree: array of dimensions len(observations) x len(observations, minimum spanning tree of all pair-wise mutual reachability distances between points.

        """

        mst = minimum_spanning_tree(dist_tree).toarray()
        return self.transpose_np(mst)

    @staticmethod
    @jit(nopython=True)
    def transpose_np(mst):
        return mst + np.transpose(mst)


    def _clustering_validity_index(self, MST, labels):

        """
        Parameters
        MST: minimum spanning tree of all pair-wisemutual reachability distances between points
        labels : 1D array with cluster labels

        Returns
        -------
        validity_index : float score in range[-1, 1] indicating validity of clustering assignments

        """
        n_samples = len(labels)
        validity_index = 0

        for label in np.unique(labels):
            fraction = np.sum(labels == label) / float(n_samples)
            cluster_validity = self._cluster_validity_index(MST, labels, label)
            validity_index += fraction * cluster_validity

        return validity_index

    def _cluster_validity_index(self, MST, labels, cluster):
        min_density_separation = np.inf
        for cluster_j in np.unique(labels):
            if cluster_j != cluster:
                cluster_density_separation = self._cluster_density_separation(MST, labels, cluster, cluster_j)
                if cluster_density_separation < min_density_separation:
                    min_density_separation = cluster_density_separation

        cluster_density_sparseness = self._cluster_density_sparseness(MST, np.array(labels), np.array(cluster))
        numerator = min_density_separation - cluster_density_sparseness
        denominator = np.max([min_density_separation, cluster_density_sparseness])
        cluster_validity = numerator / denominator
        return cluster_validity

    def _cluster_density_separation(self, MST, labels, cluster_i, cluster_j):
        indices_i = np.where(labels == cluster_i)[0]
        indices_j = np.where(labels == cluster_j)[0]
        shortest_paths = csgraph.dijkstra(MST, indices=indices_i)
        relevant_paths = shortest_paths[:, indices_j]
        density_separation = np.min(relevant_paths)
        return density_separation

    @staticmethod
    @jit(nopython=True)
    def _cluster_density_sparseness(MST, labels, cluster):
        indices = np.where(labels == cluster)[0]
        cluster_MST = MST[indices][:, indices]
        cluster_density_sparseness = np.max(cluster_MST)
        return cluster_density_sparseness

# test = DBCVCalculator(data_path='/Users/simon/Desktop/envs/troubleshooting/unsupervised/cluster_models',
#                       config_path='/Users/simon/Desktop/envs/troubleshooting/unsupervised/project_folder/project_config.ini')
# test.run()

