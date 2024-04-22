from typing import Union, Annotated
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends, HTTPException
import logging
import sys
import os
from .database import get_db, dbs
from .models import Streaming

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter("%(asctime)s  [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(stream_handler)

app = FastAPI()


async def bind_session(name: Union[str, None]) -> Union[Session, None]:
    engine_key = name.split('_')[0]
    if engine_key not in dbs().keys():
        return None
    return get_db(engine_key)


@app.get("/")
async def index():
    return JSONResponse(
        status_code=200,
        content={"success": True}
    )


@app.get("/auth")
async def auth(name: Union[str, None] = None, db: Union[Annotated[Session, None], None] = Depends(bind_session)):
    if name is None or db is None:
        raise HTTPException(status_code=422, detail="Parameter invalid")
    stream = (db.query(Streaming)
              .filter(Streaming.idStream == name)
              .first())
    if stream is None:
        raise HTTPException(status_code=422, detail="Stream not found")
    return JSONResponse(
        status_code=200,
        content={"success": True}
    )


@app.get("/end")
async def ended(name: Union[str, None] = None, db: Union[Annotated[Session, None], None] = Depends(bind_session)):
    if name is None or db is None:
        raise HTTPException(status_code=422, detail="Parameter invalid")

    os.system('chmod -R 775 /mnt')
    os.system(f'echo "#EXT-X-ENDLIST" >> /mnt/hls/{name}/index.m3u8')

    stream = (db.query(Streaming)
              .filter(Streaming.idStream == name)
              .first())
    stream.live = False
    stream.recorded = True
    # Get m3u8 and flv file url
    stream.m3u8Url = f"/hls/{name}/index.m3u8"

    for (root, _, files) in os.walk("/mnt/recordings"):
        for file in files:
            if file.startswith(name):
                stream.flvsUrl = f"/recordings/{file}"
                break

    db.commit()

    return JSONResponse(
        status_code=200,
        content={"success": True}
    )
