import os
from typing import Annotated, Union
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from dotenv import load_dotenv
load_dotenv()

from package.database import dbs, get_db, load_engine
from package.models import StreamingModel
from package.queue import run_queue
from package.utils import hls_directory
from package.logger import logger

app = FastAPI()

load_engine()
run_queue()

async def bind_session(name: Union[str, None]) -> Union[Session, None]:
    """
    This asynchronous Python function binds a session based on the provided name by extracting the
    engine key and retrieving the corresponding database.
    
    :param name: The `name` parameter is a string or None
    :type name: Union[str, None]
    
    :return: The function `bind_session` is returning either a `Session` object or `None`, depending on
    the input `name`. If the `engine_key` extracted from the `name` is not found in the keys of the
    `dbs()` dictionary, it returns `None`. Otherwise, it returns the result of calling
    `get_db(engine_key)`, which presumably returns a `Session` object.
    """
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
    """
    This Python function `auth` checks if a stream with a given name exists in a database session and
    returns a success message if found.
    
    :param name: The `name` parameter in the `auth` function is a string that represents the `idStream`
    of a `Streaming` object. It is used to query the database for a specific streaming object based on
    its `idStream`. If the `name` parameter is `None`, or if the
    :type name: Union[str, None]
    
    :param db: The `db` parameter in the `auth` function is of type `Annotated[Session, None]`. This
    means it is an optional parameter that should be either a `Session` object or `None`. The `Session`
    object is likely a database session object used for querying the database
    :type db: Union[Annotated[Session, None], None]
    
    :return: A JSONResponse object with a status code of 200 and content {"success": True} is being
    returned.
    """

    if name is None or db is None:
        logger.warning("Error authentication parameter. "
                    f'name: {name}')
        raise HTTPException(status_code=422, detail="Parameter invalid")

    stream = (db.query(StreamingModel)
              .filter(StreamingModel.idStream == name)
              .first())

    if stream is None:
        logger.warning("Error stream record not found in database. "
                       f'name: {name}')
        raise HTTPException(status_code=422, detail="Stream not found")
    return JSONResponse(
        status_code=200,
        content={"success": True}
    )


@app.get("/end")
async def ended(name: Union[str, None] = None, db: Union[Annotated[Session, None], None] = Depends(bind_session)):
    """
    This method updates a streaming record in a database, marks it as not live, and
    provides m3u8 file URLs.
    
    :param name: The `name` parameter in the `ended` function is used to identify a specific streaming
    session. It is expected to be a string representing the unique identifier of the streaming session
    that has ended
    :type name: Union[str, None]
    
    :param db: The `db` parameter in the provided code is a dependency parameter that is expected to be
    of type `Annotated[Session, None]`. It is used as a dependency injection for a database session
    object. The `Session` type is likely referring to a database session object from an ORM (Object
    :type db: Union[Annotated[Session, None], None]
    
    :return: The function `ended` is returning a JSON response with a status code of 200 and content
    indicating success. The content of the response is a dictionary with a key "success" set to True.
    """
    if os.path.isfile(f"{hls_directory}/{name}/index.m3u8"):
        with open(f"{hls_directory}/{name}/index.m3u8",  "a") as f:
            f.writelines('\n#EXT-X-ENDLIST')
            f.close()

    if name is None or db.is_active is not True:
        raise HTTPException(status_code=422, detail="Parameter invalid")

    stream = (db.query(StreamingModel)
              .filter(StreamingModel.idStream == name)
              .first())
    stream.live = False
    stream.recorded = True
    # Get m3u8 file url
    stream.m3u8Url = f"/hls/{name}/index.m3u8"

    db.commit()

    return JSONResponse(
        status_code=200,
        content={"success": True}
    )