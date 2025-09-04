import sys
from config import Config, ConfigError
from utils.helpers import is_service_available
import logging_config  # Ensures logging is configured

import logging
logger = logging.getLogger(__name__)

SERVICE_URLS = {
    'Rasa Bot': 'http://localhost:5005',
    'APIs': 'http://localhost:8000',
    'Monitoring': 'http://localhost:9090',
}

def check_services():
    all_ok = True
    for name, url in SERVICE_URLS.items():
        logger.info(f"Checking {name} at {url}...")
        if is_service_available(url):
            logger.info(f"{name} is available.")
        else:
            logger.error(f"{name} is NOT available at {url}.")
            all_ok = False
    return all_ok

def main():
    logger.info("Starting health check for Sustainable Travel Planner...")
    # Check configuration
    try:
        config = Config()
        logger.info("All required environment variables are set.")
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    # Check services
    if not check_services():
        logger.error("One or more services are not available. Please check logs and configuration.")
        sys.exit(2)
    logger.info("All services are healthy!")

if __name__ == "__main__":
    main()
