import os

# TODO: Read config from file
class Config:
    SECRET_KEY = os.environ.get('PFU_SECRET_KEY', 'dev-key-change-me')
    DATA_DIR = os.environ.get('PFU_DATA_DIR', 'data')
    UPLOAD_DIR = os.environ.get('PFU_UPLOAD_DIR', 'uploads')
    FILE_URL_PREFIX = os.environ.get('PFU_FILE_URL_PREFIX', 'f/')
    CHUNK_SIZE = int(os.environ.get('PFU_CHUNK_SIZE', 4096))
    FILENAME_LENGTH = int(os.environ.get('PFU_FILENAME_LENGTH', 5))
    HOSTNAME = os.environ.get('PFU_HOSTNAME', '0.0.0.0')
    PORT = os.environ.get('PFU_PORT', '8080')
    # Default auth secret is 'pfu'
    AUTH_SECRET = os.environ.get('PFU_AUTH_SECRET', 'scrypt:32768:8:1$ARe248ZvlIUSOZRs$8c3f5adb2984cc4ea90a31bea781e1edac6a45aa6cf5bfe5eedd7f55d6f9b12f8d7a625c8d4ca82daf03ede17f7935f7f4d9247e36f5acefc697338e754151df')
    # Default admin account (admin:password)
    ADMIN_USERNAME = os.environ.get('PFU_ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('PFU_AMIN_PASSWORD_HASH', 'scrypt:32768:8:1$vvnNBZL0bMiA9wPG$5edcc73a73eedeca672f182fc50a75c6a01f3a0fe3f9b912d33050b43a6d4e6c15d4d3ec7ab09c82ed9c31856b162eb0456f84f4baf1359d06992eed59a518f7')
