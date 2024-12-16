import logging, sys

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.WARNING)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter("%(asctime)s  [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(stream_handler)