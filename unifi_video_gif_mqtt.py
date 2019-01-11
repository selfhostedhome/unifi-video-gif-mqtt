#!/usr/bin/env python3

import sys
import json
import subprocess
import os
from collections import namedtuple
from pathlib import Path
from tempfile import mkstemp


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
        "fps=15,scale=320:-1:flags=lanczos", "-y", output_gif
    ])
    print(output_gif)


def main():
    _, new_meta_file = sys.argv
    new_meta_file = Path(new_meta_file)

    metadata = load_metadata(new_meta_file)
    metadata = parse_metadata(metadata)

    if metadata is None:
        sys.exit(1)

    video_dir = new_meta_file.parent.parent
    video_files = choose_video_files(video_dir, metadata.start, metadata.end)

    # Each video is 2 seconds long, so take 7 of them to make 14 second gif
    if len(video_files) > 7:
        video_files = video_files[:7]

    output_gif = new_meta_file.stem + '.gif'
    video_file = combine_video_files(video_files)
    convert_video_gif(video_file, output_gif)


if __name__ == "__main__":
    main()
