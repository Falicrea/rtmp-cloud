import os
import re
from typing import Union

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from package.models.stream import Stream

load_dotenv()

from package.database import retrieve_connection, load_engine, CONNECTION_DATABASE
from package.utils import hls_directory
from package.logger import logger

app = FastAPI()

load_engine()


async def bind_session(name: Union[str, None]) -> Union[Session]:
    """
    This asynchronous Python function binds a session based on the provided name by extracting the
    engine key and retrieving the corresponding database.
    
    :param name: The `name` parameter is a string or None
    :type name: Union[str, None]
    
    :return: The function `bind_session` is returning either a `Session` object or `None`, depending on
    the input `name`. If the `id` extracted from the `name` is not found in the keys of the
    `CONNECTION_DATABASE` dictionary. The function will raise an HTTPException with a status code of 400
    """
    if name is None or '_' not in name:
        raise HTTPException(status_code=400, detail="Name invalid")
    match = re.match(r"(\w+)_", name)
    if not match:
        raise HTTPException(status_code=400, detail="Name invalid")
    id = match.group(1)
    if id not in CONNECTION_DATABASE.keys():
        raise HTTPException(status_code=400, detail="Database invalid")
    return retrieve_connection(id)


@app.get("/")
async def index():
    return JSONResponse(status_code=200, content={"success": True})


@app.get("/auth")
async def auth(name: Union[str, None] = None, session: Session = Depends(bind_session)):
    if name is None:
        logger.warning("Error authentication parameter. name: {name}")
        raise HTTPException(status_code=422, detail="Parameter invalid")

    try:
        streamModel = (session.query(Stream).filter(Stream.idStream == name).first())
    except:
        raise HTTPException(status_code=428, detail="Session gone away")
    else:
        session.close()
        if streamModel is None:
            logger.warning("Error stream record not found in database. "
                           f'name: {name}')
            raise HTTPException(status_code=404, detail="Stream not found")

    return JSONResponse(status_code=200, content={"success": True})


@app.get("/end")
async def ended(name: Union[str, None] = None, session: Session = Depends(bind_session)):
    if name is None:
        logger.warning("Error authentication parameter. name: {name}")
        raise HTTPException(status_code=422, detail="Parameter name not defined")

    try:
        streamModel = session.query(Stream).filter(Stream.idStream == name).first()
    except:
        raise HTTPException(status_code=428, detail="Session gone away")
    else:
        if streamModel is not None:
            if os.path.isfile(f"{hls_directory}/{name}/index.m3u8"):
                with open(f"{hls_directory}/{name}/index.m3u8", "a") as f:
                    f.writelines('\n#EXT-X-ENDLIST')
                    f.close()
                # Get m3u8 file url
                streamModel.m3u8Url = f"/hls/{name}/index.m3u8"

            streamModel.live = False
            streamModel.recorded = True

            session.commit()
        else:
            raise HTTPException(status_code=404, detail="Stream not found")
        session.close()

    return JSONResponse(
        status_code=200,
        content={"success": True}
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=3030, log_level="info")
