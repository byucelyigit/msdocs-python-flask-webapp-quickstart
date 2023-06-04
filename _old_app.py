import os
import pandas as pd
import openai
import numpy as np
from openai.embeddings_utils import get_embedding
import json
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import datetime

import config


from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)

app = Flask(__name__)

root_dir = "c:\\Users\\burak.yucelyigit\\OneDrive\\kisisel\Yazılım\\openai\\crawler\\SemanticCatalogSearch\\"
HOST = config.settings['host']
MASTER_KEY = config.settings['master_key']
DATABASE_ID = config.settings['database_id']
CONTAINER_ID = config.settings['container_id']


@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['POST'])
def hello():
   name = request.form.get('name')
   if name:
       print('Request for hello page received with name=%s' % name)
       return render_template('hello.html', name = ReturnSomething())
   else:
       print('Request for hello page received with no name or blank name -- redirecting')
       return redirect(url_for('index'))

def SortedList(question, top):
    df_embeddings = pd.read_csv(root_dir + 'embeddings_eng.csv')    
    q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002')['data'][0]['embedding']

    # code takes the 'embedding' column in df (which contains strings representing arrays of numbers) and converts each string to a NumPy array, which is then stored in a new column called 'embedding_values'.
    df_embeddings['embedding_values'] = df_embeddings.embedding.apply(eval).apply(np.array)
    # Get the distances from the embeddings
    df_embeddings['distances'] = distances_from_embeddings(q_embeddings, df_embeddings['embedding_values'].values, distance_metric='cosine')    

    # sort values ascending. smallest distance is at top
    df_sorted = df_embeddings.sort_values('distances')
    # top n value from df_sorted
    df_top_n = df_sorted.iloc[0:top]
    # first_row_sorted = df_sorted.iloc[0]
    return df_top_n


def query_items(container, account_number):
    print('\nQuerying for an  Item by Partition Key\n')

    # Including the partition key value of account_number in the WHERE filter results in a more efficient query
    items = list(container.query_items(
        query="SELECT * FROM r WHERE r.partitionKey=@account_number",
        parameters=[
            { "name":"@account_number", "value": account_number }
        ]
    ))

    def query_items(container, account_number):

        print('\nQuerying for an  Item by Partition Key\n')

        # Including the partition key value of account_number in the WHERE filter results in a more efficient query
        items = list(container.query_items(
            query="SELECT * FROM r WHERE r.partitionKey=@account_number",
            parameters=[
                { "name":"@account_number", "value": account_number }
            ]
    ))

def read_items(container):
    print('\nReading all items in a container\n')

    # NOTE: Use MaxItemCount on Options to control how many items come back per trip to the server
    #       Important to handle throttles whenever you are doing operations such as this that might
    #       result in a 429 (throttled request)
    item_list = list(container.read_all_items(max_item_count=10))

    print('Found {0} items'.format(item_list.__len__()))

    for doc in item_list:
        print('Item Id: {0}'.format(doc.get('id')))

def ReturnSomething():
    return "result"

if __name__ == '__main__':
   app.run()
