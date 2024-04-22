FROM murderousone/nginx-ffmpeg-rtmp:ubuntu-latest

LABEL maintainer="Tiafeno Finel <tiafenofnel@gmail.com>"

RUN apt-get update && apt-get install -y curl perl fcgiwrap && rm -fr /var/lib/apt/lists/*
RUN ./start-rtmp

EXPOSE 1935
EXPOSE 447
EXPOSE 443
EXPOSE 80

CMD ["/bin/bash"]