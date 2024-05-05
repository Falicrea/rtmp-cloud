FROM murderousone/nginx-ffmpeg-rtmp:ubuntu-latest

LABEL maintainer="Tiafeno Finel <tiafenofnel@gmail.com>"

RUN apt-get update && apt-get install -y libc-dev build-essential curl perl fcgiwrap && rm -fr /var/lib/apt/lists/*

# start fcgiwrap process
RUN /etc/init.d/fcgiwrap start -f \
    && chown www-data:www-data -R /var/run/fcgiwrap.socket \
    && chmod 777 /var/run/fcgiwrap.socket

RUN usermod --non-unique --uid 1000 www-data \
    && groupmod --non-unique --gid 1000 www-data

USER www-data
    
EXPOSE 1935
EXPOSE 447
EXPOSE 443
EXPOSE 80

CMD ["/bin/bash"]