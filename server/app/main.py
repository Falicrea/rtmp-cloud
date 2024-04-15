from typing import Union
from fastapi.responses import JSONResponse
from fastapi import FastAPI
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter("%(asctime)s  [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(stream_handler)

app = FastAPI()

@app.get("/auth")
async def auth(name: Union[str, None] = None):
    logger.info(f"Streaming name %s" % name)
    return JSONResponse(
        status_code=200,
        content=""
    )
