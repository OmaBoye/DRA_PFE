# analysis/loggers.py
import logging
import os
from django.conf import settings

# Create logs directory if it doesn't exist
if not os.path.exists(settings.LOGS_DIR):
    os.makedirs(settings.LOGS_DIR)

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create file handler
fh = logging.FileHandler(os.path.join(settings.LOGS_DIR, 'analysis.log'))
fh.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# Add handler to logger
logger.addHandler(fh)