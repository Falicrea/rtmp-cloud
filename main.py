import threading
from dotenv import load_dotenv

load_dotenv('.env')

import os
import json
import re
from typing import Union
import hashlib
import subprocess

import uvicorn
from fastapi import Depends, Request, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session, sessionmaker

from package.intranet import Intranet
from package.logger import logger
from package.models.stream import Stream
from package.utils import WORK_DIR, SRT

limiter = Limiter(key_func=get_remote_address)
process_list = dict()
    
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# MediaMTX request model
class StreamRequest(BaseModel):
    user: str
    password: str
    token: str
    ip: str
    action: str # "publish|read|playback|api|metrics|pprof"
    path: str
    protocol: str # "rtsp|rtmp|hls|webrtc|srt"
    id: str
    query: str

async def bind_session(name: str) -> sessionmaker[Session]:

    """
    This asynchronous Python function binds a session based on the provided name by extracting the
    engine key and retrieving the corresponding database.
    
    :param name: The `name` parameter is a string
    :type name: str
    
    :return: The function `bind_session` is returning either a `Session` object or `None`, depending on
    the input `name`. If the `id` extracted from the `name` is not found in the keys of the
    `CONNECTION_DATABASE` dictionary. The function will raise an HTTPException with a status code of 400
    """
    if name is None or '_' not in name:
        raise HTTPException(status_code=400, detail="Name invalid")
    match = re.match(r"(\w+)_", name)
    if not match:
        raise HTTPException(status_code=400, detail="Name invalid")
    try :
        intranet = Intranet(match.group(1))
        return intranet.get_session()
    except ValueError as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=400, detail=e.__str__())

def stream_key_func(request: Request) -> str:
    """
    Génère une clé personnalisée pour le rate limiter.
    - Utilise une clé spécifique dans le request ou un hash du contenu du request.
    """
    body = request._body
    raw_key = body.decode() if body else json.dumps({"path": get_remote_address(request)})
    data = json.loads(raw_key)
    return hashlib.sha256(data['path'].encode()).hexdigest()

@app.get("/")
async def index():
    return JSONResponse(status_code=200, content={"success": True})

@app.get("/nginx-rtmp/auth")
async def ngxAuth(name: str, session: sessionmaker[Session] = Depends(bind_session)):
    with session.begin() as db:
        try:
            stream_model = db.query(Stream).filter(Stream.idStream == name).first()
        except:
            raise HTTPException(status_code=428, detail="Session gone away")
        else:
            if stream_model is None:
                logger.warning(f'Error stream record not found in database. name: {name}')
                raise HTTPException(status_code=404, detail="Stream not found")
            else:
                db.close()

    return JSONResponse(status_code=200, content={"success": True})

@app.get("/nginx-rtmp/end")
async def ngxEnded(name: str, flashver: Union[None, str] = None, session: sessionmaker[Session] = Depends(bind_session)):
    # Les relays ne sont pas autorisés
    flashver = flashver if flashver is not None else None
    if flashver is None or re.search(r"-(relay$)", flashver) is not None:
        return JSONResponse(status_code=203, content={"success": False})

    return disconnectStream(session=session, stream_key=name)

# Discution avec Claude: https://claude.ai/share/77609d1f-bdcd-428f-a0c3-3ee9cb0b4a43
@app.post("/mtx/connect")
@limiter.limit(limit_value="25/minute", key_func=stream_key_func)
async def mtxOnReady(request: Request, item: StreamRequest):
    session = await bind_session(item.path)
    with session.begin() as db:
        try:
            stream_model = db.query(Stream).filter(Stream.idStream == item.path).first()
            if not stream_model:
                raise HTTPException(status_code=500, detail="Stream not found")
            else:
                # Generate a thumbnail for the stream
                if process_list.get(stream_model.idStream) is None:
                    thumbnail_path = os.path.join(WORK_DIR, 'thumbnails', stream_model.idStream, f"thumb_%03d.jpg")
                    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                    ffmpeg_command = [
                        'ffmpeg',
                        '-i', f'srt://{SRT["host"]}:{SRT["port"]}?streamid=read:{stream_model.idStream}',
                        '-vf',
                        'fps=1/30', # Capture one frame every 30 seconds
                        thumbnail_path  # Output file path
                    ]
                    # Schedule to run after 60 seconds
                    timer = threading.Timer(60.0, run_command, args=(ffmpeg_command, stream_model.idStream))
                    timer.start()

                    process_list[stream_model.idStream] = timer

                stream_model.live = True
                db.commit()
                db.close()
                return JSONResponse(status_code=200, content={"password": "", "user": ""})
        except Exception as exc:
            logger.error(f'Error stream authentication exception: {exc}')
            
    return JSONResponse(status_code=500, content="Unauthorized")

@app.get("/mtx/disconnect")
async def mtxOnDisconnect(request: Request):
    name = request.query_params.get('name')
    session = await bind_session(name)
    # Stop thumbnail generation
    if name in process_list:
        process = process_list[name]
        if isinstance(process, subprocess.Popen):
            process.terminate()
        elif isinstance(process, threading.Timer):
            process.cancel()
        del process_list[name]
    return disconnectStream(session=session, stream_key=name)

def run_command(command: list, id: str):
    """
    Exécute une commande ffmpeg en utilisant subprocess.Popen et gère les erreurs.
    
    :param command: La commande ffmpeg à exécuter, sous forme de liste de chaînes de caractères.
    :type command: list
    """
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        output, errors = process.communicate()
        process_list[id] = process
        if process.returncode != 0:
            logger.error(f"FFmpeg error: {errors.decode()}")
        else:
            logger.info(f"FFmpeg output: {output.decode()}")
    except Exception as e:
        logger.error(f"Exception during FFmpeg execution: {e}")


def disconnectStream(session: sessionmaker[Session], stream_key: str):
    with session.begin() as db:
        try:
            stream_model = db.query(Stream).filter(Stream.idStream == stream_key).first()
            if not stream_model:
                raise HTTPException(status_code=404, detail="Stream not found")
            if stream_model.mpdUrl is not None or stream_model.m3u8Url is not None:
                return JSONResponse(status_code=200, content={"success": True, "message": "Already recorded"})
        except Exception as exc:
            raise HTTPException(status_code=428, detail="Stream not found or Session gone away") from exc
        else:
            # Get m3u8 file url
            stream_model.m3u8Url = f"/hls/{stream_key}/index.m3u8"
            stream_model.live = False
            db.commit()
            db.close()

    return JSONResponse(status_code=201, content={"success": True})


if __name__ == "__main__":
    # Check configuration file
    if not os.getenv('CONFIG_FILE') or not os.path.isfile(os.getenv('CONFIG_FILE')):
        raise ValueError("Configuration file not found")

    # Run the FastAPI application using Uvicorn
    uvicorn.run("main:app", port=3030, reload=True, log_level="info", ws="websockets", ws_max_queue=20, ws_ping_interval=10)
