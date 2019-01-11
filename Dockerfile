FROM jrottenberg/ffmpeg:4.0

ADD unifi_video_gif_mqtt.py requirements.txt /
VOLUME /config

RUN apt-get update && \
  apt-get install -y python3 python3-pip && \
  pip3 install -r /requirements.txt \
  && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/usr/bin/env"]
CMD ["python3", "/unifi_video_gif_mqtt.py", "/config/config.json"]
