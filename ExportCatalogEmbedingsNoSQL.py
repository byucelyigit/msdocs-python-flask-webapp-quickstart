import os
import pandas as pd
import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import datetime
import config
import pymongo

# Bu uygulama CosmosDB'ye veri ekleme işlemini gerçekleştirmektedir.
# komut satırından bir kez çalıştırılır.
# demelerde nosql vector verilerinin gönderilmesi ve alınması (özellikle alınması) konusunda çok yavaş kaldı.

settings = {
    'host': os.environ.get('ACCOUNT_HOST', 'https://aiexperiment.documents.azure.com:443/'),
    'master_key': os.environ.get('ACCOUNT_KEY', 'osGQ0NoqEDvY2gjfyn8fMeeA388AZzA1NVOiDxpDRSdrNnNJgg3bX90BsVrXf7FFlXZY9kkbc3N1HVx0HpU8VA=='),
    'database_id': os.environ.get('COSMOS_DATABASE', 'samplemongodb'),
    'container_id': os.environ.get('COSMOS_CONTAINER', 'vectors'),
    'collection_id': os.environ.get('COSMOS_COLLECTION', 'exampleCollection'),
}

HOST = config.settings['host']
MASTER_KEY = config.settings['master_key']
DATABASE_ID = config.settings['database_id']
CONTAINER_ID = config.settings['container_id']
COLLECTION_ID = config.settings['collection_id']

def Item(item_id, name):
    order1 = {'id' : item_id,
        'partitionKey' : 'Account1',
        'name' : name,
        }
    return order1
    
def CreateItem(item_id, name):
    client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    db = client.get_database_client(DATABASE_ID)
    container = db.get_container_client(CONTAINER_ID)
    order = Item("SalesOrder3", "test")
    container.create_item(body=order)

def EmbeddingItem(index, embedding):
    item = {'id' : index,
            'embedding' : embedding,}
    return item

def CreateEmbedingItem():
    client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    db = client.get_database_client(DATABASE_ID)
    container = db.get_container_client(CONTAINER_ID)
    embeding = EmbeddingItem("1", "[34,54,65,76,]")
    container.create_item(body=embeding)

def CreateEmbedingItems(embeddingList):
    client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    db = client.get_database_client(DATABASE_ID)
    container = db.get_container_client(CONTAINER_ID)
    for index, row in embeddingList.iterrows():
        # convert index into a string
        i = str(index)
        print(i)
        embeding = EmbeddingItem(i, row['embedding'])
        container.create_item(body=embeding)
        print("item created")


def ReadEmbeddings():
    df_embeddings = pd.read_csv('embeddings_eng.csv')    
    # write a code that show current directory
    print(os.getcwd())
    # write a code that list first four items of df_embeddings
    print(df_embeddings.head())
    # write a code that show the number of rows and columns of df_embeddings
    print(df_embeddings.shape)
    return df_embeddings
    
def ReadEmbeddingsFromCosmoDB():
    client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    db = client.get_database_client(DATABASE_ID)
    container = db.get_container_client(CONTAINER_ID)   
    item_list = list(container.read_all_items(max_item_count=100))
    print('Found {0} items'.format(item_list.__len__()))
    for doc in item_list:
        print('Item Id: {0}'.format(doc.get('id')))

# aşağıdaki fonksiyonu  bir kez çalıştırmak lazım. 
# embeddings csv dosyasındaki embeddings verilerini cosmodb'ye yazar.
def ExportEmbeddings():
    embeddingList = ReadEmbeddings()
    CreateEmbedingItems(embeddingList) 

def query_items(id):
    print('\nQuerying for an  Item by Partition Key\n')

    client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    db = client.get_database_client(DATABASE_ID)
    container = db.get_container_client(CONTAINER_ID)   

    # Including the partition key value of account_number in the WHERE filter results in a more efficient query
    items = list(container.query_items(
        query="SELECT * FROM r WHERE r.id=@id_number",
        parameters=[
            { "name":"@id_number", "value": id }
        ]
    ))

    print('Item queried by id  {0}'.format(items[0].get("id")))

def createvectorindex():
    client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    db = client.get_database_client(DATABASE_ID)
    json = {'createIndexes' : 'exampleCollection',
            'indexes': [
                {
                'name': 'vectorSearchIndex',
                'key': {
                    "vectorContent": "cosmosSearch"
                },
                'cosmosSearchOptions': {
                    'kind': 'vector-ivf',
                    'numLists': 100,
                    'similarity': 'COS',
                    'dimensions': 3
                }
                }
            ]
            }
    
    db.createindexes(json)
    return

def createmongodbvectorindex():
    # Connect to the Cosmos DB using the Azure Cosmos Client
    client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    db = client.get_database_client(DATABASE_ID)
    container = db.get_container_client("vectors")  
    # Define the index to be created
    index_name = "vectorSearchIndex"
    index_key = [("vectorContent", "cosmosSearch")]
    index_options = {
        "kind": "vector-ivf",
        "numLists": 100,
        "similarity": "COS",
        "dimensions": 3
    }
    container.createIndex(index_key, name=index_name, options=index_options)
    print("Index created successfully")

def deletemongodbrecords():
    # Connect to the Cosmos DB using the Azure Cosmos Client
    client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    db = client.get_database_client(DATABASE_ID)
    container = db.get_container_client("vectors")  
    # Delete all records in the collection
    query = "SELECT * FROM c"
    result = container.query_items(query, enable_cross_partition_query=True)

    for document in result:
        print(document['id'])        
        container.delete_item(item="1", partition_key="/")    

    print("Deleted:", result.deleted_count)
    return

def searchmongodb():
    #  aşağıdaki aslında çalışıyor ama
    # bütün kayıtları dönüyor. bunun sebebi indexin 3 embeddings
    # elemanı için tanımlanmış olması ama 
    # benim openai'dan gelen 1500 elemanı var.
    # şimdi kayıtları silip 3 elemanlı kayıtlar oluşturmaya çalışıyorum.
    # Connect to the Cosmos DB using the Azure Cosmos Client
    # client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    client = pymongo.MongoClient('mongodb+srv://byucelyigit:burak123A@vectormongo.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000')
    db = client.get_database('samplemongodb')
    collection = db['exampleCollection']
    # client = cosmos_client()

    # db = client.samplemongodb.
    # 

    # container = db.get_container_client("vectors")

    # Define the query vector
    queryVector = [0.52, 0.28, 0.12]

    pipeline = [
        {
            "$search": {
                "cosmosSearch": {
                    "vector": queryVector,
                    "path": "vectorContent",
                    "k": 2
                },
                "returnStoredSource": True
            }
        }
    ]

    result = collection.aggregate(pipeline)
    # Print the result
    for document in result:
        print(document)


# ExportEmbeddings()
# ReadEmbeddingsFromCosmoDB()  # nosql için  >700 maddeyi çekmesi epey vakit alıyor. mongodb içn biraz daha hızlı 
searchmongodb()
# createmongodbvectorindex()
# deletemongodbrecords()
# query_items("1")
# createvectorindex()
