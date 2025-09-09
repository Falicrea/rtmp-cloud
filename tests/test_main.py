import faker
from httpx import Response

from main import app
from fastapi.testclient import TestClient
from sqlalchemy import func
from faker import Faker

from package.intranet import Intranet
from package.models.stream import Stream

client = TestClient(app)

def get_random_stream():
    intranet = Intranet('sp')
    session = intranet.get_session()
    with session.begin() as db:
        stream = db.query(Stream).order_by(func.random()).first()
        assert stream is not None
        db.close()
    return stream

def test_read_index():
    response: Response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"success": True}

def test_read_ngxAuth():
    response: Response = client.get('/ngx/auth?name=test')
    assert response.status_code == 400

    response: Response = client.get('/ngx/auth?name=sp_test')
    assert response.status_code == 404

    stream = get_random_stream()
    # Verification de l'authorization
    response: Response = client.get(f'/ngx/auth?name={stream.idStream}')
    assert response.status_code == 200
    assert response.json() == {"success": True}

def test_read_ngxEnd():
    response: Response = client.get('/ngx/end?name=test')
    assert response.status_code == 400
    assert response.json() == {"detail": "Name invalid"}

    response: Response = client.get('/ngx/end?name=sp_test')
    assert response.status_code == 428

    stream = get_random_stream()
    response: Response = client.get(f'/ngx/end?name={stream.idStream}')
    assert response.status_code == 201

def test_read_mtxConnect(faker):
    stream = get_random_stream()
    data = {
        "user": "user",
        "password": faker.name(),
        "action": "publish",
        "path": stream.idStream,
        "protocol": "webrtc",
        "token": "test",
        "id": "test",
        "ip": "test",
        "query": "test"
    }
    response: Response = client.post(f'/mtx/connect', json=data, headers={"content-type": "application/json"})
    assert response.status_code == 200
