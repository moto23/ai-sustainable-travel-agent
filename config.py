import os

class ConfigError(Exception):
    pass

class Config:
    """
    Centralized configuration management for Sustainable Travel Planner.
    Loads and validates all required environment variables.
    """
    REQUIRED_VARS = [
        'OPENWEATHERMAP_API_KEY',
        'CLIMATIQ_API_KEY',
        'PINECONE_API_KEY',
        'HUGGINGFACE_API_KEY',
    ]

    def __init__(self):
        self.OPENWEATHERMAP_API_KEY = self._get_env('OPENWEATHERMAP_API_KEY')
        self.CLIMATIQ_API_KEY = self._get_env('CLIMATIQ_API_KEY')
        self.PINECONE_API_KEY = self._get_env('PINECONE_API_KEY')
        self.HUGGINGFACE_API_KEY = self._get_env('HUGGINGFACE_API_KEY')

    def _get_env(self, var_name):
        value = os.getenv(var_name)
        if not value:
            raise ConfigError(f"Environment variable '{var_name}' is missing. Please check your .env file or system environment.")
        return value

# Usage:
# from config import Config, ConfigError
# try:
#     config = Config()
# except ConfigError as e:
#     print(f"[CONFIG ERROR] {e}")
#     exit(1)
