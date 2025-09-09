from httpx import Response

from main import app
from fastapi.testclient import TestClient
from sqlalchemy import func

from package.intranet import Intranet
from package.models.stream import Stream

client = TestClient(app)

def test_read_index():
    response: Response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"success": True}

def test_read_ngxAuth():
    response: Response = client.get('/ngx/auth?name=test')
    assert response.status_code == 400
    assert response.json() == {"detail": "Name invalid"}

    response: Response = client.get('/ngx/auth?name=sp_test')
    assert response.status_code == 404
    assert response.json() == {"detail": "Stream not found"}

    intranet = Intranet('sp')
    session = intranet.get_session()
    with session.begin() as db:
        stream = db.query(Stream).order_by(func.random()).first()
        if stream is not None:
            response: Response = client.get(f'/ngx/auth?name={stream.idStream}')
            assert response.status_code == 200
            assert response.json() == {"success": True}
        db.close()

def test_read_ngxEnd():
    response: Response = client.get('/ngx/end?name=test')
    assert response.status_code == 400
    assert response.json() == {"detail": "Name invalid"}

    response: Response = client.get('/ngx/end?name=sp_test')
    assert response.status_code == 428