#!/usr/bin/env python3

import sys
import json
import subprocess
import os
from collections import namedtuple
from pathlib import Path
import time
from tempfile import mkstemp
from collections import deque

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import paho.mqtt.client as mqtt


def load_metadata(metadata_file):
    with metadata_file.open('r') as meta_file:
        metadata = json.load(meta_file)
    return metadata


def parse_metadata(metadata):
    if metadata["eventType"] != "motionRecording":
        return None
    if metadata["inProgress"]:
        return None

    Recording = namedtuple('recording', ['name', 'start', 'end'])
    return Recording(metadata["meta"]["cameraName"],
                     str(metadata["startTime"]), str(metadata["endTime"]))


def choose_video_files(video_dir, start, end):
    videos = video_dir.glob("*.mp4")
    videos = sorted(list(videos))

    found_start = False
    video_clips = []
    for video in videos:
        if video.name.startswith(start):
            found_start = True
            video_clips.append(video)
        elif video.name.startswith(end):
            video_clips.append(video)
            break
        elif found_start:
            video_clips.append(video)

    return video_clips


def combine_video_files(video_clips):
    _, video_file_list = mkstemp(
        prefix='unifi_video_gif_mqtt_videos.', suffix='.txt')
    _, video_file_mp4 = mkstemp(
        prefix='unifi_video_gif_mqtt_videos.', suffix='.mp4')

    with open(video_file_list, 'w') as f:
        for video in video_clips:
            f.write("file '{}'\n".format(video))

    subprocess.call([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", video_file_list,
        "-c", "copy", video_file_mp4
    ])

    os.remove(video_file_list)
    return video_file_mp4


def convert_video_gif(input_video, output_gif):
    subprocess.call([
        "ffmpeg", "-i", input_video, "-vf",
        "fps=15,scale=320:-1:flags=lanczos", "-y",
        str(output_gif)
    ])
    os.remove(input_video)


def parse_config(config_path):
    with open(config_path, 'r') as config_file:
        config_data = json.load(config_file)
    return config_data


class UniFiVideoEventHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config

        self.mqtt_client = mqtt.Client()

        # Keep a FIFO of files processed so we can guard against duplicate
        # filesystem events
        self.processed_files = deque(maxlen=20)
        super().__init__()

    def on_any_event(self, event):
        print(event)

    def on_modified(self, event):
        modified_file = Path(event.src_path)
        if modified_file.suffix == ".json" and modified_file.parent.name == "meta":
            gif, camera_name = self.convert_gif(modified_file)
            if gif:
                self.publish_mqtt_message(gif, camera_name)

    def convert_gif(self, metadata_file):
        output_gif = Path(
            self.config["gif_output_dir"]).joinpath(metadata_file.stem +
                                                    '.gif')

        # Make sure we didn't get a duplicate filesystem event and process
        # something we already processed
        if output_gif in self.processed_files:
            return None, None

        metadata = load_metadata(metadata_file)
        metadata = parse_metadata(metadata)

        if metadata is None:
            return None, None

        video_dir = metadata_file.parent.parent
        video_files = choose_video_files(video_dir, metadata.start,
                                         metadata.end)

        # Each video is 2 seconds long, so take 7 of them to make 14 second gif
        if len(video_files) > 7:
            video_files = video_files[:7]

        video_file = combine_video_files(video_files)
        convert_video_gif(video_file, output_gif)

        # Add to list of processed files
        self.processed_files.append(output_gif)

        return output_gif, metadata.name

    def publish_mqtt_message(self, gif, camera_name):
        self.mqtt_client.connect(self.config["mqtt_server"],
                                 self.config["mqtt_port"])
        ret = self.mqtt_client.publish(
            self.config["mqtt_base_topic"] + "/" + camera_name, gif.name)


def main():
    _, config_filename = sys.argv
    config = parse_config(config_filename)

    event_handler = UniFiVideoEventHandler(config)
    observer = Observer()
    observer.schedule(
        event_handler, config["unifi_video_watch_dir"], recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
