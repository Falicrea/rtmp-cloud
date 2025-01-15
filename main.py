from dotenv import load_dotenv
load_dotenv('.env')

import re, os
from typing import Union

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, sessionmaker
from package.models.stream import Stream

from package.intranet import Intranet
from package.utils import hls_directory, mpd_directory
from package.logger import logger


app = FastAPI()

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


@app.get("/")
async def index():
    return JSONResponse(status_code=200, content={"success": True})


@app.get("/auth")
async def auth(name: str, session: sessionmaker[Session] = Depends(bind_session)):
    with session.begin() as db:
        try:
            stream_model = db.query(Stream).filter(Stream.idStream == name).first()
        except:
            raise HTTPException(status_code=428, detail="Session gone away")
        else:
            if stream_model is None:
                db.close()
                logger.warning(f'Error stream record not found in database. name: {name}')
                raise HTTPException(status_code=404, detail="Stream not found")
            else:
                db.close()

    return JSONResponse(status_code=200, content={"success": True})


@app.get("/end")
async def ended(name: str, flashver: Union[None, str] = None, session: sessionmaker[Session] = Depends(bind_session)):
    # Les relays ne sont pas autorisés
    flashver = flashver if flashver is not None else ''
    if re.search(r"-(relay$)", flashver) is not None:
        return JSONResponse(status_code=203, content={"success": False})

    with session.begin() as db:
        try:
            stream_model = db.query(Stream).filter(Stream.idStream == name).first()
            if not stream_model:
                raise HTTPException(status_code=404, detail="Stream not found")
            
            if stream_model.mpdUrl is not None or stream_model.m3u8Url is not None:
                db.close()
                return JSONResponse(status_code=200, content={"success": True, "message": "Already recorded"})
                
        except Exception as exc:
            db.close()
            raise HTTPException(status_code=428, detail="Stream not found or Session gone away") from exc
        else:
            if os.path.isfile(f"{hls_directory}/{name}/index.m3u8"):
                with open(f"{hls_directory}/{name}/index.m3u8", "a", encoding="utf-8") as f:
                    f.writelines('\n#EXT-X-ENDLIST')
                    f.close()
                # Get m3u8 file url
                stream_model.m3u8Url = f"/hls/{name}/index.m3u8"

            if os.path.isfile(f"{mpd_directory}/{name}/index.mpd"):
                # Get mpd file url
                stream_model.mpdUrl = f"/dash/{name}/index.mpd"
            else:
                stream_model.mpdUrl = None
                logger.info(f"MPD file not found for {name} at {mpd_directory}/{name}/index.mpd")

            stream_model.live = False
            db.commit()
            db.close()

    return JSONResponse(status_code=201, content={"success": True})

if __name__ == "__main__":
    # Check configuration file
    if not os.getenv('CONFIG_FILE') or not os.path.isfile(os.getenv('CONFIG_FILE')):
        raise ValueError("Configuration file not found")

    # Check if HLS directory exists
    if os.getenv('MEDIA_HLS') and not os.path.isdir(hls_directory):
        raise ValueError("HLS folder doesn't exist")


    # Run the FastAPI application using Uvicorn
    uvicorn.run("main:app", port=3030, reload=True, log_level="info", ws="websockets", ws_max_queue=20, ws_ping_interval=10)
