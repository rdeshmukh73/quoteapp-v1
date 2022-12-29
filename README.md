# quoteapp-v1
First Version of the QuoteApp in Python

Python, Flask based program to: 
a. Read a Google BigQuery Database (can be any other DB as well) which stores 1000s of Popular Quotes (Source: Kaggle)
b. Provides APIs to:
  1. Get All Quotes as a Table
  2. Get a Random Quote as a Text
  3. Add a New Quote to the Database, with input provided as a JSON
 c. Requires a GCP Service Account JSON to run since it uses GCP BQ APIs
 
 This is a version created to learn the usage of Flask, Python, Pandas Dataframes and GCP BQ APIs. 
