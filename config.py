import os

settings = {
    'host': os.environ.get('ACCOUNT_HOST', 'https://aiexperiment.documents.azure.com:443/'),
    'master_key': os.environ.get('ACCOUNT_KEY', 'osGQ0NoqEDvY2gjfyn8fMeeA388AZzA1NVOiDxpDRSdrNnNJgg3bX90BsVrXf7FFlXZY9kkbc3N1HVx0HpU8VA=='),
    'database_id': os.environ.get('COSMOS_DATABASE', 'ToDoList'),
    'container_id': os.environ.get('COSMOS_CONTAINER', 'Items'),
}