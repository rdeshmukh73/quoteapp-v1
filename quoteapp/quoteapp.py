#include the required Libraries
from google.cloud import bigquery
import pandas as pd
from flask import Flask, render_template, request, jsonify, make_response
from datetime import datetime
import random
import hashlib

#Setup the BQ Client
client = bigquery.Client()

#Define Table details
table_id = "deshmukhr-cep.TESTRD.Quotes"

# Create a Flask App
app = Flask(__name__)

#Routine to get Current Time
def getCurrTime():
    now = datetime.now()
    current_time = now.strftime("%d/%m/%Y %H:%M:%S")
    return current_time

#Generates a Unique SHA256 ID using the Quote, Author and Current Time to establish uniqueness
def getUniqueID(quote, author):
    hashInput = quote + author + getCurrTime()
    hashString = hashlib.sha256(hashInput.encode('utf-8')).hexdigest()
    return hashString

#Routine to add a Quotes DataFrame to the Big Query DB Table
def addDFToDB(quotesDF:pd.DataFrame):
    job_config = bigquery.LoadJobConfig()#write_disposition=”WRITE_APPEND” to Append the Data
    job = client.load_table_from_dataframe(quotesDF, table_id, job_config=job_config) 
    # Make an API request.
    job.result()  # Wait for the job to complete.

#Routine to add one Quote to the Database
def addQuoteToDB(row_to_insert):
    errors = client.insert_rows_json(table_id, row_to_insert)  # Make an API request.
    return errors

#Routine to Get the Quotes from the DB and send it in a Dataframe
def getQuotesDF():
    df = pd.DataFrame()
    df = client.list_rows(table_id).to_dataframe()
    return df

#Global Object (oops!!!) to store the Quotes DataFrame
quotesDF = getQuotesDF()

@app.route('/')
def home():
    quotesDF.count()
    return render_template('index.html')

@app.route('/getAllQuotes')
def getAllQuotes():
    return render_template('table.html', tables=[quotesDF.to_html()], titles=[''])

@app.route('/getRandomQuote')
def getRandomQuote():
    randInt = random.randint(0, 3000)
    print(randInt)
    row = quotesDF.loc[randInt]
    randomQuote = row["Quote"]
    quoteAuthor = row["Author"]
    quoteText = f"{randomQuote} - {quoteAuthor}"
    return jsonify (quoteText)

@app.route('/addQuote', methods=['POST'])
def addQuote():
    quoteJSON = request.get_json()
    if 'Quote' not in quoteJSON:
        return make_response('Quote is required', 400)
    if 'Author' not in quoteJSON:
        return make_response('Author is required', 400)   
    quote = quoteJSON['Quote']
    author = quoteJSON['Author']
    source = quoteJSON['Source']
    tags = quoteJSON['Tags']
    likes = quoteJSON['Likes']

    uniqueID = getUniqueID(quote, author)
    quoteData = [{"ID":uniqueID, "Quote":quote[0:1047], "Author":author, "Source":source, "Tags":tags, "Likes":likes}]   

    errors = addQuoteToDB(quoteData)

    if errors == []:
        return make_response('Quote Data Saved in DB', 200)
    else:
        errorMessage = f"Error while Saving Quote Data - {errors}"
        return make_response(errorMessage, 400)


if __name__ == '__main__':
    port = 5000 
    app.run(debug=True, host='0.0.0.0', port=port)
