import requests
import json
from linkedinauth import  headers, auth

# Set the API endpoint URL
API_ENDPOINT = 'https://api.linkedin.com/v2/ugcPosts'
API_ENDPOINT = 'https://api.linkedin.com/v2/shares'
# Replace ACCESS_TOKEN with your actual access token
#ACCESS_TOKEN = "AQWRkOmidsKkUGfeXqS3jjMVh2C0bf8dRaD1a7A4sPqbmlALGr08PAc4hB0IkpH8gLWeG2WaoyPjIlilTf9xlsUILPh2OoE7wZmobP4hOm6pthuzeiVCgQL9J_wrIEIMAq_7L-uJY6tkvQSccmuLe9JmgBv6JN0-UdzLLPS_HHkW4wON9hwHOrAo6xWFqCFZH97rBIn7ZvndNBZRMA13eTTVtBZUoROyKNX_geVuDLz3CB5bF0AkweOoLeNVcL0XQsgCZbrIZZSeqSwh-Sb-Zfoacr5IvnSNSSE9HGb0qwcn_agKJM2dD02GNQxM1RAhciWpp74A_TGD6LFNuGgkEw9wWuSfgA"


def user_info(headers):
    #Get user information from Linkedin
    response = requests.get('https://api.linkedin.com/v2/me', headers = headers)
    user_info = response.json()
    return user_info
 
def getAccessToken(credentialsFile):
    access_token = ""
    with open(credentialsFile) as f:
        credentials = json.load(f)
    access_token = credentials['access_token']        
    return access_token

def postQuoteToLinkedin(quoteText):
    credentials = 'credentials.json'
    #access_token = auth(credentials) # Authenticate the API
    access_token = getAccessToken(credentials)
    if access_token == "":
        print("LinkedIn Access Token is Empty.  Cannot proceed.")
        return False

    #headers = headers(access_token) # Make the headers to attach to the API call.

    # Set the request headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'cache-control': 'no-cache',
        'X-Restli-Protocol-Version': '2.0.0'
        }

    # Get user id to make a UGC post
    user = user_info(headers)
    urn = user['id']
     
    # UGC will replace shares over time.
    author = f'urn:li:person:{urn}'


    payloadText = quoteText
    print(f'Payload for LinkedIn is: {payloadText}')
    payload = {
        "owner": author,
        "text": {
            "text": payloadText
        }
    }

    # Make the POST request
    response = requests.post(API_ENDPOINT, json=payload, headers=headers)

    # Print the response status code
    print(f"LinkedIn API Response is: {response.status_code} -- {response.text}")
    return True


#ret = postQuoteToLinkedin("This is a sample Text for Linkedin")