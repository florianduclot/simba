# SimBA Unsupervised Classification

## Overview

[highlight features of unsupervised vs. supervised, explain tutorial scenario and how this continues from prior analysis and Kleinberg, how to navigate from existing GUI]. The SimBA Unsupervised Classification pipeline and GUI were created by [Simon Nilsson](https://github.com/sronilsson) and [Aasiya Islam](https://github.com/aasiya-islam).

## Pipeline

Training an unsupervised classifier involves the creation of an algorithm that clusters animal activity based on behavioral similarities, typically with three main steps: data pre-processing, dimensionality reduction, and cluster assignment. 
The SimBA Unsupervised Classification pipeline consists of six main steps: 

**1) Save Project Folder**- allows user to create an unsupervised project folder and saves outputs to future steps in encompassed folder     
**2) Create Dataset**- cleans and pre-processes the machine results and localizes relevant data into a single dataset      
**3) Perform Dimensionality Reduction**- allows user to select a dimensionality reduction algorithm to apply and visualize data with     
**4) Perform Clustering**- assigns and visualizes clusters with HDBSCAN from the dimensionality reduction results       
**5) Train Model**- trains model on the clusters generated previously and saves permutational importance and feature correlation metrics     
**6) Visualize Clusters**- visualize behavioral bouts corresponding to clusters as original video clips or simulated skeleton movements

The outputs generated from each step can be saved into their respective folders encompassed within the main unsupervised project folder and taken as inputs for subsequent steps throughout the pipeline.

## Step 1: Save Project Folder 

<p align="center">
<img src="https://github.com/sgoldenlab/simba/blob/master/images/create_folder.PNG" />
</p>

The first step allows the user to create and save a project folder for their unsupervised analysis results. 
For each subsequent step in the pipeline, the individual outputs will save into that step's respective folder that is automatically created upon the use of each step. 

To save a project folder, specify the folder path where you would like the project folder to be saved into by clicking the ```Browse Folder``` button and selecting a folder, as the folder path will replace the ```No folder selected``` box, and designate a name for the project folder with the ```Project Name``` entry box. 
Note that the folder name will save as "unsupervised_projectname" with "projectname" being the name you filled out the entry box with. After you have specified the folder path and designated a project name, click the ```Create folder``` button to save the folder.

[insert GIF tutorial]

## Step 2: Create Dataset

<p align="center">
<img src="https://github.com/sgoldenlab/simba/blob/master/images/create_dataset.PNG" />
</p>

The second tab will walk you through pre-processing and cleaning the data from prior machine results, and saving the data relevant for unsupervised analysis into a single dataset. 
This step serves to extract behavioral bouts of interest as designated by the classifier and find mean feature values while dropping all features that are not relevant.

To begin, first import a folder of the machine results saved as CSV datasets by clicking the ```Browse Folder``` button and selecting the folder of datasets. An example of the machine results folder and CSV format and can be shown below, and is generated as directed by this documentation (hyperlink relevant documentation, discuss kleinberg or link documentation]



<p align="center">
<img src="https://github.com/sgoldenlab/simba/blob/master/images/dataset_folder2.PNG" />
</p>

<p align="center">
<img src="https://github.com/sgoldenlab/simba/blob/master/images/machine_results.PNG" />
</p>


Next, import the file that lists the features that you would like to remove or disregard in the classification. 
The purpose of this is to perform the classification without the irrelevant features (double check this) and drop them before saving our condensed dataset for future analysis. 
You can similarly select the ```Browse File``` button to search for and select this file, and the file should be formatted similar to as shown below.

<p align="center">
<img src="https://github.com/sgoldenlab/simba/blob/master/images/features2remove.PNG" />
</p>


Finally, input the name of the classifier you would like to focus your analysis on, such as "Attack" in the ```Classifier name``` entry box. Note the formatting of this name should match that depicted in the machine results or prior analysis.

Once everything has been imported, you can begin the pre-processing by clicking the ```Generate/save dataset``` button. 

>**Note:** This step may take a few minutes to process all of the machine results depending on the length and number of datasets in the folder. Once everything has been processed you will see the .pkl file 

Once everything has been processed, you will observe that a new folder labeled 'create_dataset' has been saved in your project folder, and inside the 'create_dataset' folder, there will be a single .pkl file saved under the name of the classifier you inputted, such as "Attack.pkl". The .pkl file is a serialized object file that can be read in and deserialized in future steps to use in our classification, and is mainly used for storage efficiency. It cannot be opened on its own like you would a CSV file. 

[insert pic of pkl file saved]


[GIF of saving dataset then showing pkl file saved]


## Step 3: Perform Dimensionality Reduction

<p align="center">
<img src="https://github.com/sgoldenlab/simba/blob/master/images/perform_DR.PNG" />
</p>

The third tab will walk you through selecting a dimensionality reduction algorithm and inputting hyperparameters for the respective algorithm. Dimensionality reduction is used in unsupervised learning to transform the data from high-dimension to low-dimension by reducing the number of variables/features while still maintaining data integrity and retaining meaningful properties of the intrinsic dimension. Here, it is useful for our visualization of the data as pre-processed and generated in the previous step and gives us our first glimpse of data relationships prior to clustering in the next step. 

We have provided 3 options for dimensionality reduction algorithms to choose from and use in your analysis, being [UMAP](https://umap-learn.readthedocs.io/en/latest/), [t-SNE](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html), and [PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html). Each has their own set of hyperparameters to perform the dimensionality reduction with, as outlined below, but can be inputted in the same manner. 

>**Note:** To read more about the supporting documentation for each of the hyperparameters, please click on the algorithm name and follow the hyperlink. 

First, import the pre-processed feature dataset as was saved as a .pkl file from the previous step by clicking the ```Browse File``` button and navigating to the 'create_dataset' folder. 

Next, specify the target group you would like to focus on for the analysis in the ```Target group``` entry box, such as "RI Male". [more info on target group].

Then, you can select between your dimensionality reduction algorithms via the dropdown menu on the right of the `Select dimensionality reduction algorithm` label, and by clicking the small box inside of the box that says `UMAP` (which is the default algorithm), the other options should be available. As each algorithm is selected, a new set of hyperparameter entry boxes will appear respective to the algorithm. 

For each entry box of hyperparameters, you can list several options for each hyperparameter that you would like to test in a pseudo grid search approach. A grid search is a method for hyperparameter optimization where test several hyperparameters at once as a grid of values then evaluate every position on the grid as a different combination of hyperparameters. Our approach goes through each hyperparameter value and assesses the combinations individually. You may then evaluate each combination of hyperparameters once the dimensionality reduction visualization saves in the folder and assess the effectiveness of each hyperparameter and test out other combinations to fine-tune your approach. 

<p>
<img src="https://github.com/sgoldenlab/simba/blob/master/images/UMAP.PNG" />
</p>


- UMAP: For UMAP, there are 4 hyperparameters to input, and 

<p>
<img src="https://github.com/sgoldenlab/simba/blob/master/images/tsne.PNG" />
</p>


- t-SNE:

<p>
<img src="https://github.com/sgoldenlab/simba/blob/master/images/PCA.PNG" />
</p>


- PCA:


## Step 4: Perform Clustering

<p align="center">
<img src="https://github.com/sgoldenlab/simba/blob/master/images/perform_clustering.PNG" />
</p>

## Step 5: Train Model

<p align="center">
<img src="https://github.com/sgoldenlab/simba/blob/master/images/train_model.PNG" />
</p>

## Step 6: Visualize Clusters 

<p align="center">
<img src="https://github.com/sgoldenlab/simba/blob/master/images/visualize_clusters.PNG" />
</p>