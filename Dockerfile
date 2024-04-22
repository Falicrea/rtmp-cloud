FROM murderousone/nginx-ffmpeg-rtmp:ubuntu-latest

LABEL maintainer="Tiafeno Finel <tiafenofnel@gmail.com>"

RUN apt-get update && apt-get install -y curl perl fcgiwrap && rm -fr /var/lib/apt/lists/*
RUN ./start-rtmp

# start fcgiwrap process
RUN /etc/init.d/fcgiwrap start -f \
    && chown www-data:www-data -R /var/run/fcgiwrap.socket \
    && chmod 777 /var/run/fcgiwrap.socket

EXPOSE 1935
EXPOSE 447
EXPOSE 443
EXPOSE 80

CMD ["/bin/bash"]