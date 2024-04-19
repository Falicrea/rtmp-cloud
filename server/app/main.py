from typing import Union
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends, HTTPException
import logging
import sys
import os
from .database import SessionLocal, Streaming

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter("%(asctime)s  [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(stream_handler)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/auth")
async def auth(name: Union[str, None] = None, db: Session = Depends(get_db)):
    if name is None:
        raise HTTPException(status_code=422, detail="Parameter invalid")
    stream = db.query(Streaming).filter(Streaming.idStream == name).first()
    if stream is None:
        raise HTTPException(status_code=422, detail="Stream not found")
    return JSONResponse(
        status_code=200,
        content={"success": True}
    )

@app.get("/end")
async def auth(name: Union[str, None] = None, db: Session = Depends(get_db)):
    if name is None:
        raise HTTPException(status_code=422, detail="Parameter invalid")
    os.system('chmod -R 775 /mnt')
    os.system(f'echo "#EXT-X-ENDLIST" >> /mnt/hls/{name}/index.m3u8')
    return JSONResponse(
        status_code=200,
        content={"success": True}
    )
