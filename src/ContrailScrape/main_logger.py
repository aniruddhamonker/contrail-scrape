import logging
from logging.handlers import RotatingFileHandler
import time

logger = logging.getLogger('main_logger')
fh = logging.handlers.RotatingFileHandler("/var/log/scrape-{}.log".format(time.strftime('%Y-%m-%d-%H:%M:%S-%Z'), maxBytes=100000, backupCount=5))
# console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
# console_handler.setFormatter(formatter)
logger.addHandler(fh)
# logger.addHandler(console_handler)
logger.setLevel(logging.INFO)