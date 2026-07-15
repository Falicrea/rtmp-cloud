import os
from urllib.parse import urlparse

WORK_DIR = os.getenv('WORK_DIR', '/var/www/html/stream')
SRT = {
  "host": os.getenv('SRT_SERVER_HOST', 'localhost'),
  "port": int(os.getenv('SRT_SERVER_PORT', '8890'))
}
CODECS = {
    "video": os.getenv('VIDEO_CODEC', 'libx264'),
    "audio": os.getenv('AUDIO_CODEC', 'aac')
}

# Secret partagé exigé sur les endpoints internes (/mtx/restream, /mtx/disconnect).
# Ces endpoints sont appelés par MediaMTX (runOnNotReady) ou le backend applicatif,
# jamais par un client externe. Vide => fail-closed (tout appel est refusé).
MTX_INTERNAL_SECRET = os.getenv('MTX_INTERNAL_SECRET', '')

# Allowlist anti-SSRF des destinations de rediffusion RTMP. Suffixes de domaine
# autorisés (séparés par des virgules). Empêche la redirection d'un flux vers un
# serveur RTMP arbitraire. Par défaut : plateformes sociales usuelles.
RTMP_ALLOWED_HOSTS = tuple(
    host.strip().lower()
    for host in os.getenv(
        'RTMP_ALLOWED_HOSTS',
        'rtmp.youtube.com,youtube.com,twitch.tv,live-video.net,facebook.com',
    ).split(',')
    if host.strip()
)


def validate_rtmp_url(rtmp: str) -> tuple[bool, str]:
    """
    Valide une URL de rediffusion RTMP contre l'allowlist (anti-SSRF).

    Retourne (True, "") si l'URL est acceptée, sinon (False, raison).
    Vérifie : schéma rtmp/rtmps, présence d'un hôte, et hôte appartenant à
    (ou sous-domaine de) l'un des suffixes autorisés.
    """
    try:
        parsed = urlparse(rtmp)
    except ValueError:
        return False, "malformed URL"

    if parsed.scheme not in ('rtmp', 'rtmps'):
        return False, "scheme must be rtmp or rtmps"

    host = (parsed.hostname or '').lower()
    if not host:
        return False, "missing host"

    for allowed in RTMP_ALLOWED_HOSTS:
        if host == allowed or host.endswith('.' + allowed):
            return True, ""

    return False, "destination host not allowed"