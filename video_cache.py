import argparse
import json
import os
import re
import subprocess
import sys

def get_video_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)


def create_video_list(directory):
    video_dict = {}
    with os.scandir(directory) as videos:
        file_regex = re.compile(r'^[0-9]+-(.+)-([^.]{11})\.([a-z0-9.]+)$')
        for file in videos:
            match = file_regex.match(file.name)
            if not match:
                continue

            matched_id = match.group(2)
            ext = match.group(3)
            video_item = video_dict.setdefault(matched_id, {
                'video': ('', 0, 0, 0),
                'thumbnail': '',
                'description': '',
                'view_count': 0
            })
            if ext == 'mp4':
                file_stat = file.stat()
                video_item['title'] = match.group(1)
                try:
                    length = get_video_length(file.path)
                except ValueError:
                    print('Video corrupted', file.name, file=sys.stderr)
                    length = 0
                video_item['video'] = (file.name, file_stat.st_mtime, file_stat.st_size, length)
            elif ext in ('jpg', 'webp'):
                video_item['thumbnail'] = file.name
            elif ext == 'description':
                video_item['description'] = file.name
            elif ext == 'info.json':
                with open(file.path) as f:
                    info_json = json.load(f)
                    video_item['view_count'] = info_json['view_count']

    return video_dict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('videos', help='Videos\' folder')
    parser.add_argument('video_cache', help='Resulting cache file')
    args = parser.parse_args()

    video_dict = create_video_list(args.videos)
    with open(args.video_cache, 'w') as f:
        json.dump(video_dict, f)

if __name__ == '__main__':
    main()
