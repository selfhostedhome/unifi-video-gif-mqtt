# unifi-video-gif-mqtt

Watch your UniFi Video directory for new videos, convert to gif and notify over MQTT.

Read my [blog article](https://selfhostedhome.com/unifi-video-motion-detection-gif-notifications) for a tutorial on how to get started.

## Config File

Needs a simple JSON based config file passed in on the command line.

For example:

```json
{
    "mqtt_server": "192.168.1.2",
    "mqtt_port": 1883,
    "mqtt_base_topic": "cameras/gifs",
    "gif_output_dir": "/gifs",
    "unifi_video_watch_dir": "/unifi-video"
}

```

* `mqtt_server`: MQTT server to publish notifications to
* `mqtt_port`: Port of MQTT server
* `mqtt_base_topic`: MQTT topic to publish new GIFs to. Camera name will be appended to the end of this base topic.
* `gif_output_dir`: Directory to put the created GIFs
* `unifi_video_watch_dir`: Directory to watch for new UniFi Video Recordings

## Installation

There is a docker image if you prefer to run using docker. For example:

```shell
docker run -v $(pwd)/config:/config \
    -v /srv/storage/Videos/Surveillance:/unifi-video \
    -v /tmp/gifs:gifs \
    zlalanne/unifi-video-gif-mqtt:latest
```

or via docker compose.

```yaml
services:
  unifi-video-gif-mqtt:
    image: zlalanne/unifi-video-gif-mqtt:latest
    volumes:
      - ./config/unifi-video-gif-mqtt:/config
      - /srv/storage/Videos/Surveillance:/unifi-video
      - /tmp/gifs:/gifs
    restart: unless-stopped
```

If you'd prefer to install dependencies yourself, you'll need:

* ffmpeg 4.0 (other versions probably work, but that's what I tested with)
* Python 3
* python libraries listed in `requirements.txt` (install via `pip install -r requirements.txt`)
