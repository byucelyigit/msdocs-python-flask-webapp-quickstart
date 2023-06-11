import os
import config
import pymongo
import pandas as pd
import numpy as np
from dotenv import load_dotenv


MONGO_CONNECTION_STRING = ""
DATABASE_ID = "EnoctaSemanticSearch"
COLLECTION_ID_EMBEDDINGS = "CatalogEmbeddings"
COLLECTION_ID_CATALOG_DESC = "CatalogDesc"


def LoadEnvVariables():
    global MONGO_CONNECTION_STRING
    # Get the path to the directory this file is in
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    # Connect the path with your '.env' file name
    load_dotenv(os.path.join(BASEDIR, 'configvars.env'))    
    MONGO_CONNECTION_STRING = os.getenv("AZURE_MONGODB_CONNECTION_STRING")


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
        print("Course record created")
    return


def Init():
    # --------------------------------------------
    # aşağıdaki işlemlerden önce ilgili azure resource tanımlarının yapılmış olması gerekir. Bunun için azurecli dizinindeki dosya kullanılır.
    # Aşağıdaki kısım bir kez çalıştırılır.
    # 0.
    # azure cli komutları ile resource oluşturulur.
    # create database and collection
    # 1.
    LoadEnvVariables()
    # 2.
    CreateEmbeddingsDatabase()
    # 3.
    ExportEmbeddings()  
    # 4. 
    CreateEmbeddingsVectorIndex()
    # --------------------------------------------
    CreateCourse()

    print("----------- init is complete -----------")

Init()
