import os

# TODO: Read config from file
class Config:
    SECRET_KEY = os.environ.get('PFU_SECRET_KEY', 'dev-key-change-me')
    DATABASE = os.environ.get('PFU_DATABASE', 'database.db')
    UPLOAD_DIR = os.environ.get('PFU_UPLOAD_DIR', 'uploads')
    FILE_URL_PREFIX = os.environ.get('PFU_FILE_URL_PREFIX', 'f/')
    CHUNK_SIZE = int(os.environ.get('PFU_CHUNK_SIZE', 4096))
    # Default auth secret is 'pfu'
    AUTH_SECRET = os.environ.get('PFU_AUTH_SECRET', 'scrypt:32768:8:1$ARe248ZvlIUSOZRs$8c3f5adb2984cc4ea90a31bea781e1edac6a45aa6cf5bfe5eedd7f55d6f9b12f8d7a625c8d4ca82daf03ede17f7935f7f4d9247e36f5acefc697338e754151df')
