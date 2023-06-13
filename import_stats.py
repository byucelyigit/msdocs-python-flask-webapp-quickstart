import os
import pandas as pd
import pymongo
from dotenv import load_dotenv

"""
insanların sordukları soruların ve cevapların listesini bir csv dosyasına kaydeder.
"""

MONGO_CONNECTION_STRING = ""
DATABASE_ID = "EnoctaSemanticSearch"
COLLECTION_ID_LOGS = "questionlogs"

def LoadEnvVariables():
    global MONGO_CONNECTION_STRING
    # Get the path to the directory this file is in
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    # Connect the path with your '.env' file name
    print(BASEDIR)
    load_dotenv(os.path.join(BASEDIR, 'configvars.env'))    
    MONGO_CONNECTION_STRING = os.getenv("AZURE_MONGODB_CONNECTION_STRING")

def export_logs_to_csv():
    # Connect to MongoDB

    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
    db = client[DATABASE_ID]
    collection = db[COLLECTION_ID_LOGS]

    # Retrieve all documents from the collection
    documents = list(collection.find())

    # Create a DataFrame from the documents
    df = pd.DataFrame(documents)

    # Export DataFrame to CSV
    df.to_csv(os.path.join(BASEDIR, 'logs.csv'), index=False)

    print("Logs exported to logs.csv successfully!")

# Call the function to export logs to CSV
LoadEnvVariables()
export_logs_to_csv()
