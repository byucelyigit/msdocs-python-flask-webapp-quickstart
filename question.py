import os
import pandas as pd
import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import config
import numpy as np
import pymongo
import openai
from dotenv import load_dotenv




# https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search
# yukarıdaki adresteki javascript komutları
# mongodb üzerinde çalıştırılır.
# ilk olarak azure_cli dizinindeki oluşturma cli komutları çalıştırılır. 
# bu komutlar Azure tarafındaki ortamı hazırlar.
# iş bitince yine aynı dizindeki resourceları kaldıran komut çalıştırılır.
# azure kaynakları hazır olunca init.py ile DB oluşturma ve embeddings export işlemleri yapılır.


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

def CreateEmbeddingsVectorIndex():
    # Connect to the Cosmos DB using the Azure Cosmos Client
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING )
    db = client.get_database(DATABASE_ID)

    index_spec = [
    ('vectorContent', 'text')  # Specify the field and its type in a tuple
    ]

    # Create the index
    db[COLLECTION_ID_EMBEDDINGS].create_index(index_spec, name='vectorSearchIndex', cosmosSearchOptions={
        'kind': 'vector-ivf',
        'numLists': 100,
        'similarity': 'COS',
        'dimensions': 1536
    })
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

#-------------------------------------------------------------------------
#yukarısı deneysel kodlar

def CreateEmbeddingsDatabase():
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING )
    db=client[DATABASE_ID]
    db.create_collection(COLLECTION_ID_EMBEDDINGS)

def ReadEmbeddings():
    df_embeddings = pd.read_csv('embeddings_eng.csv')    
    # write a code that show current directory
    print(os.getcwd())
    # write a code that list first four items of df_embeddings
    print(df_embeddings.head())
    # write a code that show the number of rows and columns of df_embeddings
    print(df_embeddings.shape)
    return df_embeddings

# aşağıdaki fonksiyonu  bir kez çalıştırmak lazım. 
# embeddings csv dosyasındaki embeddings verilerini cosmodb'ye yazar.
def ExportEmbeddings():
    print("ExportEmbeddings")
    embeddingList = ReadEmbeddings()
    CreateEmbedingItems(embeddingList) 

#
def CreateEmbedingItems(embeddingList):
    print("CreateEmbedingItems")
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
    db = client.get_database(DATABASE_ID)
    # collection = db['Catalog']
    # limited_df = embeddingList.head(2)
    for index, row in embeddingList.iterrows():
        # convert index into a string
        i = str(index+1)
        print("index:") 
        print(i)
        embeding = EmbeddingItem(row['index'], row['embedding'])
        db[COLLECTION_ID_EMBEDDINGS].insert_one(embeding)
        print("item created")

def EmbeddingItem(index, embedding):
    embedding_array = np.array(eval(embedding))
    item = {'id' : index,
            'vectorContent' : embedding_array.tolist()}
    return item

def GenerateQuestionEmbeddings():
    # aşağıdaki ap_key bilgisinin gihub'a gönderilmiyor olması lazım. 
    # ek olarak mongodb connection string gibi bilgilerin de gönderilmiyor olması lazım. 
    print("OpenAI Connection")
    openai.organization = OPENAI_ORG_ID 
    openai.api_key = OPENAI_APIKEY    

    print("Generate Question Embeddings")
    # question = "Elinizde kadınlara yönelik bir şeyler var mı?"

    # aşağıdaki sorunun 710 ve 68 index üretmesi gerekir
    # 
    question = "toplantıları daha verimli yönetmek mümkün mü?"  
    q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002')['data'][0]['embedding']

    print(q_embeddings[:2])

    print("Connect to mongodb")
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
    db = client.get_database(DATABASE_ID)    

    pipeline = [
        {
            "$search": {
                "cosmosSearch": {
                    "vector": q_embeddings,
                    "path": "vectorContent",
                    "k": 2
                },
                "returnStoredSource": True
            }
        }
    ]
    print("Searching...")
    result = db[COLLECTION_ID_EMBEDDINGS].aggregate(pipeline)
    # Print the result
    print("Search resut:")
    for document in result:
        print(document['id'])
        r = document['id']
    return r

def deleteEmbeddings():
    print("Connect to mongodb")
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
    # db = client.get_database('EnoctaEmbeddings')  
    client.drop_database(DATABASE_ID)
    print("Database dropped")

def CreateCourse():
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING )
    db=client[DATABASE_ID]
    db.create_collection(COLLECTION_ID_CATALOG_DESC)
    df_coursedata = pd.read_csv('katalog.csv', sep=';')    
    # write a code that show current directory
    print(os.getcwd())
    # write a code that list first four items of df_embeddings
    print(df_coursedata.head())
    # write a code that show the number of rows and columns of df_embeddings
    print(df_coursedata.shape)

    for index, row in df_coursedata.iterrows():
        # convert index into a string
        i = str(index+1)
        print("index:") 
        print(i)
        item = {'id'     : row['index'],
                'header' : row['header'],
                'desc'   :row['desc']
            }
        db[COLLECTION_ID_CATALOG_DESC].insert_one(item)
        print("item created")
    return

# index listesi verilen kursların bilgilerini mongodb'den bulup df olarak döner.
def Context(df_indexes):
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING )
    db=client[DATABASE_ID] 
    items = list(db[COLLECTION_ID_CATALOG_DESC].query_items(
    query="SELECT * FROM r WHERE r.id=@id_number",
    parameters=[
        { "name":"@id_number", "value": df_indexes[0] }
    ]
    ))

    print('Item queried by id  {0}'.format(items[0].get("id"))) 

def Init():
    # --------------------------------------------
    # aşağıdaki işlemlerden önce ilgili azure resource tanımlarının yapılmış olması gerekir. Bunun için azurecli dizinindeki dosya kullanılır.
    # Aşağıdaki kısım bir kez çalıştırılır.
    # 1.
    # azure cli komutları ile resource oluşturulur.
    # create database and collection
    # 2.
    CreateEmbeddingsDatabase()
    # 3.
    ExportEmbeddings()  
    # 4. 
    CreateEmbeddingsVectorIndex()
    # --------------------------------------------
    CreateCourse()


MONGO_CONNECTION_STRING = ""
DATABASE_ID = "EnoctaSemanticSearch"
COLLECTION_ID_EMBEDDINGS = "CatalogEmbeddings"
COLLECTION_ID_CATALOG_DESC = "CatalogDesc"
OPENAI_ORG_ID = ""
OPENAI_APIKEY = ""

def LoadEnvVariables():
    global MONGO_CONNECTION_STRING
    global OPENAI_ORG_ID
    global OPENAI_APIKEY
    # Get the path to the directory this file is in
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    # Connect the path with your '.env' file name
    print(BASEDIR)
    load_dotenv(os.path.join(BASEDIR, 'configvars.env'))    
    MONGO_CONNECTION_STRING = os.getenv("AZURE_MONGODB_CONNECTION_STRING")
    OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
    OPENAI_APIKEY = os.getenv("OPENAI_APIKEY")
    # print(MONGO_CONNECTION_STRING)
    # print(OPENAI_ORG_ID)
    # print(OPENAI_APIKEY)

LoadEnvVariables()
#result = Context([710, 68])
#print(result)
#deleteEmbeddings()
# Init()
# ReadEmbeddingsFromCosmoDB()  # nosql için  >700 maddeyi çekmesi epey vakit alıyor. mongodb içn biraz daha hızlı 
# searchmongodb()
GenerateQuestionEmbeddings()
# createmongodbvectorindex()
# deletemongodbrecords()
# query_items("1")
# createvectorindex()
# deleteEmbeddings()

