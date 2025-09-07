import os

WORK_DIR = os.getenv('WORK_DIR', '/var/www/html/stream')
SRT = {
  "host": os.getenv('SRT_SERVER_HOST', 'localhost'),
  "port": int(os.getenv('SRT_SERVER_PORT', '8890'))
}