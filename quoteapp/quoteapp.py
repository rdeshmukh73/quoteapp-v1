from google.cloud import bigquery
import pandas as pd
from flask import Flask, render_template, request, jsonify, make_response
from datetime import datetime
import random
import hashlib
import json
from flask_cors import CORS
from google.cloud import pubsub_v1
from postQuoteToLinkedin import postQuoteToLinkedin

# Create a Flask App
app = Flask(__name__)
CORS(app)

# Set up the Cloud Pub/Sub client
publisher = pubsub_v1.PublisherClient()
# Get the topic handle
project = 'deshmukhr-cep'
topic_name = 'rdtopic1'
# Setup the Topic Path to Publish the Information
topic_path = publisher.topic_path(project, topic_name)

# Initialize the JSON Encoder object
js = json.JSONEncoder()

#Setup the BQ Client
client = bigquery.Client()

#Define Table details
table_id = "deshmukhr-cep.TESTRD.Quotes"

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
    #job_config = bigquery.LoadJobConfig(write_disposition='WRITE_APPEND',create_disposition='CREATE_NEVER',streaming=True,publish_callback=topic.publish)
    
    errors = client.insert_rows_json(table_id, row_to_insert) #, job_config=job_config)  # Make an API request.
    return errors

#function to send Quote Data to a Pub/Sub Topic --> Not in use
def publishToTopic(quoteData):
    # We need to Encode it (default utf-8) to be sent to the Pub/Sub Topic
    pubsub_data = js.encode(quoteData)
    pubsub_data = pubsub_data.encode()
    print(pubsub_data)
    # Send it to the Pub/Sub Topic
    future = publisher.publish(topic_path, pubsub_data)


#Routine to Get the Quotes from the DB and send it in a Dataframe
def getQuotesDF():
    df = pd.DataFrame()
    df = client.list_rows(table_id).to_dataframe()
    return df

#Global Object (oops!!!) to store the Quotes DataFrame
quotesDF = getQuotesDF()

#On successful addition of a new Quote to the DB, the same will be updated to the Cache - quotesDF
def updateQuotesDF(quoteData):
    global quotesDF
    tempDF = pd.DataFrame(quoteData)
    print(tempDF)
    quotesDF = pd.concat([quotesDF, tempDF])
    quotesDF = quotesDF.reset_index(drop=True)


#Default: Renders Index.html
@app.route('/')
def home():
    return render_template('index.html')

#Gets all quotes and presents them in a Table
@app.route('/getAllQuotes')
def getAllQuotes():
    return render_template('table.html', tables=[quotesDF.to_html()], titles=[''])

#Gets a Random Quote
@app.route('/getRandomQuote')
def getRandomQuote():
    randInt = random.randint(0, 3000)
    print(randInt)
    row = quotesDF.loc[randInt]
    randomQuote = row["Quote"]
    quoteAuthor = row["Author"]
    #quoteText = f"{randomQuote} - {quoteAuthor}"
    quoteText = {"Quote":randomQuote, "Author":quoteAuthor}
    
    response = jsonify (quoteText)
    # Enable Access-Control-Allow-Origin
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

#Adds a New Quote to the Database
@app.route('/addQuote', methods=['POST'])
def addQuote():
    quoteJSON = request.get_json()
    print(quoteJSON)
    if 'Quote' not in quoteJSON:
        return make_response('Quote is required', 400)
    if 'Author' not in quoteJSON:
        return make_response('Author is required', 400)   
    quote = str(quoteJSON['Quote'])
    author = str(quoteJSON['Author'])
    source = quoteJSON['Source']
    tags = quoteJSON['Tags']
    likes = quoteJSON['Likes']

    uniqueID = getUniqueID(quote, author)
    quoteData = [{"ID":uniqueID, "Quote":quote[0:1047], "Author":author, "Source":source, "Tags":tags, "Likes":likes}]   

    errors = addQuoteToDB(quoteData)

    # Set the CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': '*'
    }
    
    if errors == []:
        #pub_response = publishToTopic(quoteData)
        updateQuotesDF(quoteData)
        response = make_response('Quote Data Saved in DB', 200)
    else:
        errorMessage = f"Error while Saving Quote Data - {errors}"
        response = make_response(errorMessage, 400)
    return response

#Get the Basic details of the # of Quotes, # of Authors
@app.route('/getBasicDetails', methods=['GET'])
def getBasicDetails():
    uniqueAuthors = len(pd.unique(quotesDF['Author'])) #Get unique Authors. https://www.geeksforgeeks.org/how-to-count-distinct-values-of-a-pandas-dataframe-column/
    totalQuotes = len(quotesDF.axes[0]) #Get the count of Rows
    quotesBasicInfo = {"TotalQuotes":totalQuotes, "UniqueAuthors":uniqueAuthors}
    print(quotesBasicInfo)
    response = jsonify(quotesBasicInfo)
    # Enable Access-Control-Allow-Origin
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route('/getAuthorList', methods=['GET'])
def getAuthorList():
    uniqueAuthors = pd.unique(quotesDF['Author'])
    uniqueAuthors.sort()
    
    authorList = json.dumps(uniqueAuthors.tolist())
    response = make_response(authorList, 200)
    # Enable Access-Control-Allow-Origin
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

#To post a Quote to LinkedIn
@app.route('/postQuoteToLinkedIn', methods=['POST'])
def postQuoteToLinkedIn():
    quote = request.data.decode()
    print(quote)
    if postQuoteToLinkedin(quote) == True:
        return make_response("Posting to LinkedIn Successful", 200)
    else:
        return make_response("Failed to Post to LinkedIn", 400)    


#To find a Random Quote From a chosen Author
@app.route('/getRandomQuoteForAuthor/<author>', methods=['GET'])
def getRandomQuoteForAuthor(author):
    indexArray = []
    for index, row in quotesDF.iterrows():
        if row['Author'] == author:
            indexArray.append(index)
    
    randInt = random.randint(0,len(indexArray)-1)      
    print(randInt)
    rowID = indexArray[randInt]
    print(rowID)
    quoteText = quotesDF.loc[rowID]['Quote']
    quoteResponse = {'Quote': quoteText}
    response = make_response(quoteResponse, 200)
    # Enable Access-Control-Allow-Origin
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
    
    '''
    quoteRow = quotesDF.loc[quotesDF['Author'] == author]
    print(type(quoteRow))
    jsontext = quoteRow.to_json()
    print(jsontext)
    jsontext = json.loads(jsontext)
    print(type(jsontext))
    '''
    '''
    quoteText = quoteRow['Quote']
    print(type(quoteText))
    str = quoteText.to_string()
    print(str)
    print(type(str))
    '''



if __name__ == '__main__':
    port = 5000 
    app.run(debug=True, host='0.0.0.0', port=port)
