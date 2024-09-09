import logging, sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter("%(asctime)s  [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(stream_handler)