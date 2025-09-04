import logging
import sys

# Configure logging for the entire project
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_LEVEL = logging.INFO

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Usage:
# import logging
# logger = logging.getLogger(__name__)
# logger.info('This is an info message')
