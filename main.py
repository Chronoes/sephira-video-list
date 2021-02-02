import argparse
import collections
import datetime
import html
import json
import math
import os
import os.path
import random
import re
import string
import subprocess
import sys
from urllib.parse import quote

from video_cache import create_video_list

def unbounded_shuffle_gen(initlist):
    list_copy = initlist[:]
    random.shuffle(list_copy)
    last_item = initlist[-1]
    while True:
        if last_item == list_copy[0]:
            list_copy.append(list_copy.pop(0))
        yield from list_copy
        last_item = list_copy[-1]

class VideoTemplate:
    def __init__(self, **templates):
        self.templates = {}
        for template in templates:
            with open(templates[template]) as f:
                self.templates[template] = string.Template(f.read())
        self.placeholders = unbounded_shuffle_gen([
            '/assets/sephira_closewink.webp',
            '/assets/sephira_smile.webp',
            '/assets/sephira_surprise.webp',
            '/assets/sephira_upturned.webp',
            '/assets/sephira_yandere.webp'
        ])

    def create_html(self, template, **kwargs):
        return self.templates[template].substitute(kwargs)

    def create_playlist_html(self, **kwargs):
        return self.create_html('playlist',
            title=kwargs['title'],
            placeholder=next(self.placeholders),
            thumbnail=html.escape(quote(kwargs['thumbnail'])),
            videos_href=html.escape(quote(kwargs['videos']))
        )

    def create_video_html(self, video_item):
        (video, mtime, size, video_length) = video_item['video']

        return self.create_html('video',
            title=video_item['title'],
            placeholder=next(self.placeholders),
            thumbnail=html.escape('/' + quote(video_item['thumbnail'])),
            video=html.escape('/' + quote(video)),
            timestamp=mtime,
            date=datetime.datetime.fromtimestamp(mtime).strftime('%b %d, %Y %H:%M'),
            video_size=human_readable_size(size),
            video_length=human_readable_time(video_length),
            description_href=html.escape('/' + video_item['description'])
        )

def human_readable_time(total_seconds):
    (mins, secs) = divmod(total_seconds, 60)
    (hrs, mins) = divmod(mins, 60)
    if hrs > 0:
        return f'{int(hrs)}:{int(mins):02}:{int(secs):02}'
    return f'{int(mins)}:{int(secs):02}'

size_formats = ['B', 'KiB', 'MiB', 'GiB']
def human_readable_size(size_bytes):
    power = int(math.log(size_bytes, 1024))
    return f'{round(size_bytes / (1024 ** power), 1)} {size_formats[power]}'


def sort_videos_and_playlists(playlist, video_dict):
    videos = []
    playlists = []
    for entry in playlist['playlists_and_ids']:
        if type(entry) == str:
            if entry in video_dict:
                videos.append(video_dict[entry])
            else:
                print('Could not find', entry, 'in input folder', file=sys.stderr)
        else:
            sort_videos_and_playlists(entry, video_dict)
            playlists.append(entry)

    playlist['videos'] = videos
    playlist['playlists'] = playlists
    return playlist

def write_playlist_html(root_playlist, video_dict, video_tpl, output_folder, write_to_file=True):
    print('Creating HTML for', root_playlist['title'])
    playlists_html = ''

    for pl in root_playlist['playlists']:
        sort_videos_and_playlists(pl, video_dict)

        if len(pl['playlists']) > 0:
            write_playlist_html(pl, video_dict, video_tpl, output_folder)

        if len(pl['videos']) > 0:
            print('Creating videos HTML for', pl['title'])
            videos_html = write_videos_html(pl, video_tpl, output_folder)
            if pl['title'] == 'Uploads':
                root_playlist['index_videos'] = videos_html

        thumbnail = ''
        if len(pl['videos']) > 0:
            thumbnail = '/' + pl['videos'][0]['thumbnail']
        elif len(pl['playlists']) > 0 and len(pl['playlists'][0]['videos']) > 0:
            thumbnail = '/' + pl['playlists'][0]['videos'][0]['thumbnail']

        filename = pl['title'] + '.html'
        playlists_html += video_tpl.create_playlist_html(
            title=pl['title'],
            thumbnail=thumbnail,
            videos='/' + filename
        )

    playlists_html = video_tpl.create_html('playlists_section', playlists=playlists_html)

    if write_to_file:
        filename = root_playlist['title'] + '.html'
        with open(os.path.join(output_folder, filename), 'w') as f:
            f.write(video_tpl.create_html('main',
                content=playlists_html,
                header_title=root_playlist['title'],
                metatitle=root_playlist['title'] + ' - Sephira Su')
            )

    return playlists_html


def write_videos_html(playlist, video_tpl, output_folder):
    filename = playlist['title'] + '.html'

    videos_html = video_tpl.create_html(
        'videos_section',
        videos=''.join(video_tpl.create_video_html(item) for item in playlist['videos'])
    )
    with open(os.path.join(output_folder, filename), 'w') as f:
        f.write(video_tpl.create_html('main', content=videos_html, header_title=playlist['title'], metatitle=playlist['title'] + ' - Sephira Su'))

    return videos_html


def argument_parser():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--video-cache', help='Cache file for video and related files like description and thumbnail')
    group.add_argument('--videos', help='Unprocessed videos\' folder')

    parser.add_argument('playlist', help='Playlists JSON')
    parser.add_argument('output', help='Output folder for HTML files')
    return parser

def main():
    parser = argument_parser()
    args = parser.parse_args()

    if args.videos:
        video_dict = create_video_list(args.videos)
    else:
        with open(args.video_cache) as f:
            video_dict = json.load(f)

    video_tpl = VideoTemplate(
        main='main.tpl.html',
        playlists_section='playlists_section.tpl.html',
        playlist='playlist.tpl.html',
        videos_section='videos_section.tpl.html',
        video='video.tpl.html'
    )

    with open(args.playlist) as f:
        root_playlist = {
            'title': 'Videos',
            'playlists': json.load(f),
            'videos': [],
            'index_videos': ''
        }
    playlists_html = write_playlist_html(root_playlist, video_dict, video_tpl, args.output, write_to_file=False)
    filename = 'index.html'
    with open(os.path.join(args.output, filename), 'w') as f:
        f.write(video_tpl.create_html('main',
            content=playlists_html + '<h2>Uploads</h2>' + root_playlist['index_videos'],
            header_title='Videos by Sephira Su',
            metatitle='Videos archive - Sephira Su')
        )

if __name__ == '__main__':
    main()
