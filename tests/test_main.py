import random

import pytest
from httpx import Response

import main
from main import app
from fastapi.testclient import TestClient
from sqlalchemy import func

from package.intranet import Intranet, PrefixNotAuthorized
from package.models.stream import Stream

client = TestClient(app)

INTERNAL_SECRET = "test-internal-secret"


@pytest.fixture
def internal_secret(monkeypatch):
    """Configure un secret interne pour les endpoints /mtx internes (S2).

    `require_internal_auth` lit la globale `main.MTX_INTERNAL_SECRET` ; on la
    patche le temps du test (auto-restaurée par monkeypatch)."""
    monkeypatch.setattr(main, "MTX_INTERNAL_SECRET", INTERNAL_SECRET)
    return INTERNAL_SECRET


def auth_header(secret: str = INTERNAL_SECRET) -> dict:
    return {"Authorization": f"Bearer {secret}"}

def get_random_stream():
    # Sélection aléatoire de la base parmi les préfixes configurés (plutôt qu'en
    # dur) : on essaie chaque base dans un ordre aléatoire et on retourne le
    # premier stream trouvé, ce qui tolère une base vide.
    prefixes = Intranet.available_prefixes()
    assert prefixes, "aucun préfixe de base configuré"
    random.shuffle(prefixes)
    for prefix in prefixes:
        session = Intranet(prefix).get_session()
        with session.begin() as db:
            stream = db.query(Stream).order_by(func.random()).first()
            if stream is not None:
                return stream
    pytest.skip("aucun stream disponible dans les bases configurées")

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

    data.update({"path": "invalid_stream"})
    response: Response = client.post(f'/mtx/connect', json=data)
    assert response.status_code != 200

def test_command_ffmpeg():
    # Verifier si la commande ffmpeg est accessible sur la machine
    import shutil
    ffmpeg_path = shutil.which("ffmpeg")
    assert ffmpeg_path is not None
    assert shutil.which("ffmpeg") == ffmpeg_path


# --- S5 : cloisonnement des bases par table d'autorisation -------------------

def test_ngxauth_strict_prefix():
    # Extraction stricte du préfixe : un préfixe non [a-z0-9] est rejeté (400).
    response: Response = client.get('/ngx/auth?name=SP_test')
    assert response.status_code == 400
    assert response.json() == {"detail": "Name invalid"}


def test_resolve_prefix_rejects_unknown():
    # Un préfixe non autorisé (absent de la config / table `prefixes`) est refusé.
    with pytest.raises(PrefixNotAuthorized):
        Intranet.resolve_prefix('unconfigured_prefix_xyz')


# --- S2 : endpoints internes (auth partagée + allowlist RTMP + POST) ---------

def test_disconnect_is_post_only():
    # /mtx/disconnect est passé en POST : le GET n'existe plus.
    response: Response = client.get('/mtx/disconnect?name=sp_test')
    assert response.status_code == 405


def test_disconnect_fail_closed_without_secret():
    # Secret interne non configuré (.env vide) => fail-closed 503.
    assert main.MTX_INTERNAL_SECRET == ""
    response: Response = client.post('/mtx/disconnect?name=sp_test')
    assert response.status_code == 503


def test_disconnect_requires_bearer(internal_secret):
    # Secret configuré mais header absent / invalide => 401.
    response: Response = client.post('/mtx/disconnect?name=sp_test')
    assert response.status_code == 401

    response = client.post('/mtx/disconnect?name=sp_test',
                           headers=auth_header("wrong-secret"))
    assert response.status_code == 401


def test_disconnect_auth_ok_then_validates_name(internal_secret):
    # Header valide => l'auth passe ; un name sans underscore échoue en aval (400).
    response: Response = client.post('/mtx/disconnect?name=test',
                                     headers=auth_header())
    assert response.status_code == 400
    assert response.json() == {"detail": "Name invalid"}


def test_restream_fail_closed_without_secret():
    response: Response = client.post(
        '/mtx/restream',
        json={"rtmp": "rtmp://a.rtmp.youtube.com/live2/KEY", "name": "sp_x"},
    )
    assert response.status_code == 503


def test_restream_requires_bearer(internal_secret):
    response: Response = client.post(
        '/mtx/restream',
        json={"rtmp": "rtmp://a.rtmp.youtube.com/live2/KEY", "name": "sp_x"},
    )
    assert response.status_code == 401


def test_restream_rejects_non_allowlisted_rtmp(internal_secret):
    # Auth OK mais destination hors allowlist => 400 (anti-SSRF).
    response: Response = client.post(
        '/mtx/restream',
        headers=auth_header(),
        json={"rtmp": "rtmp://evil.example.com/live/KEY", "name": "sp_x"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "RTMP URL invalid"}