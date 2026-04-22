import logging
import os
import tomllib
from dataclasses import dataclass

# Do not change values here - use environment variables or config.toml instead
DEFAULTS: dict[str, str | int | bool] = {
    'SECRET_KEY': 'dev-key-change-me',
    'DATA_DIR': 'data',
    'UPLOAD_DIR': 'uploads',
    'FILE_URL_PREFIX': 'http://localhost:8080/files/',
    'CHUNK_SIZE': 65536,
    'FILENAME_LENGTH': 5,
    'UPDATE_STATS_INTERVAL': 1,  # In hours
    'INTEGRITY_CHECK_INTERVAL': 24,  # In hours
    'HOSTNAME': '0.0.0.0',
    'PORT': '8080',
    'LOG_LEVEL': 'INFO',
    'INDEX_REDIRECT': '/home',
    # Default admin account (admin:password)
    'ADMIN_USERNAME': 'admin',
    'ADMIN_PASSWORD': 'scrypt:32768:8:1$vvnNBZL0bMiA9wPG$5edcc73a73eedeca672f182fc50a75c6a01f3a0fe3f9b912d33050b43a6d4e6c15d4d3ec7ab09c82ed9c31856b162eb0456f84f4baf1359d06992eed59a518f7'
}

logger = logging.getLogger(__name__)


# Config class for Flask compatibility
@dataclass
class ConfigClass:
    SECRET_KEY: str
    DATA_DIR: str
    UPLOAD_DIR: str
    FILE_URL_PREFIX: str
    CHUNK_SIZE: int
    FILENAME_LENGTH: int
    UPDATE_STATS_INTERVAL: int
    INTEGRITY_CHECK_INTERVAL: int
    HOSTNAME: str
    PORT: int
    LOG_LEVEL: str
    INDEX_REDIRECT: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str


def load_config() -> ConfigClass:
    config = DEFAULTS.copy()
    env_prefix = 'PFU_'
    data_dir = os.environ.get(f'{env_prefix}DATA_DIR', config['DATA_DIR'])
    if not isinstance(data_dir, str):
        data_dir = str(data_dir)
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
    # Coerce known integer fields
    int_fields = ['CHUNK_SIZE', 'FILENAME_LENGTH', 'UPDATE_STATS_INTERVAL', 'INTEGRITY_CHECK_INTERVAL', 'PORT']
    for field in int_fields:
        if field in config:
            try:
                config[field] = int(config[field])
            except (ValueError, TypeError):
                logger.warning(f"Could not convert {field} value '{config[field]}' to int, using default.")
                config[field] = DEFAULTS[field]
    # Roughly validate INDEX_REDIRECT
    index_redirect = config['INDEX_REDIRECT']
    if not isinstance(index_redirect, str) or not index_redirect.startswith('/') or index_redirect == '/':
        logger.warning(f"INDEX_REDIRECT '{index_redirect}' must be a valid path starting with '/', using default '/home'.")
        config['INDEX_REDIRECT'] = '/home'
    # This should always be type safe
    return ConfigClass(**config)  # type: ignore


config = load_config()

# Security warnings for default values
security_warnings = []
if config.SECRET_KEY == DEFAULTS['SECRET_KEY']:
    msg = 'SECRET_KEY is using default value!'
    logger.warning(msg)
    security_warnings.append(msg)
if config.ADMIN_USERNAME == DEFAULTS['ADMIN_USERNAME']:
    msg = 'ADMIN_USERNAME is using default value!'
    logger.warning(msg)
    security_warnings.append(msg)
if config.ADMIN_PASSWORD == DEFAULTS['ADMIN_PASSWORD']:
    msg = 'ADMIN_PASSWORD is using default value!'
    logger.warning(msg)
    security_warnings.append(msg)
