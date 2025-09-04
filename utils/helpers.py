import os
import logging

logger = logging.getLogger(__name__)

def get_env_variable(name, default=None, required=False):
    """
    Retrieve an environment variable and handle errors.
    Args:
        name (str): Name of the environment variable.
        default: Default value if not set.
        required (bool): If True, raise error if not set.
    Returns:
        str: Value of the environment variable.
    Raises:
        EnvironmentError: If required and not set.
    """
    value = os.getenv(name, default)
    if required and value is None:
        logger.error(f"Required environment variable '{name}' is missing.")
        raise EnvironmentError(f"Required environment variable '{name}' is missing.")
    return value

def is_service_available(url):
    """
    Check if a service is available at the given URL.
    Args:
        url (str): Service URL.
    Returns:
        bool: True if service is reachable, False otherwise.
    """
    import requests
    try:
        response = requests.get(url, timeout=3)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Service at {url} is not available: {e}")
        return False
