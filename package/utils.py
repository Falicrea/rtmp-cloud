import os

hls_directory = os.getenv('MEDIA_HLS', '/var/www/hls')
mpd_directory = os.getenv('MEDIA_MPD', '/var/www/mpd')