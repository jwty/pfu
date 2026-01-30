import logging
import os
import tomllib

DEFAULTS = {
    'SECRET_KEY': 'dev-key-change-me',
    'DATA_DIR': 'data',
    'UPLOAD_DIR': 'uploads',
    'FILE_URL_PREFIX': 'https://change.me/files/',
    'CHUNK_SIZE': 65536,
    'FILENAME_LENGTH': 5,
    'UPDATE_STATS_INTERVAL': 1,  # In hours
    'HOSTNAME': '0.0.0.0',
    'PORT': '8080',
    'LOG_LEVEL': 'INFO',
    # Default admin account (admin:password)
    'ADMIN_USERNAME': 'admin',
    'ADMIN_PASSWORD': 'scrypt:32768:8:1$vvnNBZL0bMiA9wPG$5edcc73a73eedeca672f182fc50a75c6a01f3a0fe3f9b912d33050b43a6d4e6c15d4d3ec7ab09c82ed9c31856b162eb0456f84f4baf1359d06992eed59a518f7'
}

logger = logging.getLogger(__name__)


# Config class for Flask compatibility
class ConfigClass(object):
    def __init__(self, config_dict):
        for key, value in config_dict.items():
            setattr(self, key, value)


def load_config():
    config = DEFAULTS.copy()
    env_prefix = 'PFU_'
    data_dir = os.environ.get(f'{env_prefix}DATA_DIR', config['DATA_DIR'])
    config_file = os.path.join(data_dir, 'config.toml')
    # Override defaults with config file
    if os.path.isfile(config_file):
        try:
            with open(config_file, 'rb') as file:
                config.update(tomllib.load(file))
        except (tomllib.TOMLDecodeError, OSError) as e:
            logger.error(f"could not load config file: {e}")
    # Override with env vars (they have highest priority)
    for key in config.keys():
        env_var = f'{env_prefix}{key}'
        if env_var in os.environ:
            config[key] = os.environ[env_var]
    return config


config_dict = load_config()
config = ConfigClass(config_dict)
