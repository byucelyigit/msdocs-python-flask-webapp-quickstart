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


def GenerateQuestionEmbeddings(question):
    # aşağıdaki ap_key bilgisinin gihub'a gönderilmiyor olması lazım. 
    # ek olarak mongodb connection string gibi bilgilerin de gönderilmiyor olması lazım. 
    print("OpenAI Connection")
    openai.organization = OPENAI_ORG_ID 
    openai.api_key = OPENAI_APIKEY    

    print("Generate Question Embeddings")
    # question = "Elinizde kadınlara yönelik bir şeyler var mı?"

    # aşağıdaki sorunun 710 ve 68 index üretmesi gerekir
    # 
    # question = "toplantıları daha verimli yönetmek mümkün mü?"  
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
    print("Search results:")
    list = []
    for document in result:
        print(document['id'])
        list.append(document['id'])
    return list

def deleteEmbeddings():
    print("Connect to mongodb")
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
    # db = client.get_database('EnoctaEmbeddings')  
    client.drop_database(DATABASE_ID)
    print("Database dropped")

# index listesi verilen kursların bilgilerini mongodb'den bulup df olarak döner.
def Answer(question):
    print("Most related course search")

    # Convert list to DataFrame
    results = GenerateQuestionEmbeddings(question)
    
    print("Answer generation")
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING )
    db=client[DATABASE_ID] 
    query = {"id": {"$in": results}}
    cursor = db[COLLECTION_ID_CATALOG_DESC].find(query)

    found_items = list(cursor)

    desc =""
    course_header = ""
    print("Related Courses:")
    print("------------------------------")
    if found_items:
        for item in found_items:
            # print('Item queried by id: {0}'.format(item.get("header")))
            course_header = course_header + "* " + item.get("header") + "\n"
            desc = desc + item.get("desc")
    else:
        print('No items found.')
    print("Question Context:")
    print("-----------------------------------")
    print(desc)
    # desc bilgisi openAI'a soru ile birlikte gönderilir.

    print("OpenAI Connection")
    openai.organization = OPENAI_ORG_ID 
    openai.api_key = OPENAI_APIKEY   

    response = openai.Completion.create(
                prompt=f"Soruya aşağıdaki içeriğe göre cevap ver. Eğer sorunun cevabı içerikte yer almıyorsa o zaman \"Sorunuza doğrudan cevap veremiyorum ama size çeşitli eğitim ve okuma başlığı önerebilirim.\" şeklinde cevap ver. \n\nİçerik: {desc}\n\n---\n\nSoru: {question}\nCevap:",
                temperature=0,
                max_tokens=250,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                model="text-davinci-003"
            )
    response = "------\n\nQuestion: " + question + "\n\n" + "Response: " +  response["choices"][0]["text"].strip() + "\n\nAşağıda bu konuyla ilgili eğitim önerileri yer almaktadır:\n\n" + course_header
    #print(response)  # + url) 
    """
    print("\nHere are the course names:")
    print("---------------------------")
    if found_items:
        for item in found_items:
            print("* " + item.get("header"))
    """
    return response




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
result = Answer("yarın yönetime yapacağım sunumu nasıl daha iyi yapabilirim?")
print(result)
#deleteEmbeddings()
# Init()
# ReadEmbeddingsFromCosmoDB()  # nosql için  >700 maddeyi çekmesi epey vakit alıyor. mongodb içn biraz daha hızlı 
# searchmongodb()
# GenerateQuestionEmbeddings()
# createmongodbvectorindex()
# deletemongodbrecords()
# query_items("1")
# createvectorindex()
# deleteEmbeddings()

