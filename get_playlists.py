import json
import subprocess
import sys


def fetch_playlist_output(url_or_id):
    return subprocess.run(['youtube-dl', '--cookies', '.cookies-youtube-com.txt', '-j', '--flat-playlist', url_or_id], capture_output=True, text=True)

def fetch_playlist(url_or_id):
    root_playlist = fetch_playlist_output(url_or_id)
    print('Downloading playlist', url_or_id)

    playlists = []
    for line in root_playlist.stdout.splitlines():
        playlist = json.loads(line)
        if 'id' in playlist and len(playlist['id']) == 11:
            playlists.append(playlist['id'])
            continue

        filtered_pl = {}
        for key in ['id', 'url', 'title']:
            if key in playlist:
                filtered_pl[key] = playlist[key]

        filtered_pl['playlists_and_ids'] = fetch_playlist(playlist['url'])

        playlists.append(filtered_pl)

    return playlists


playlists = fetch_playlist(sys.argv[1])
with open('playlists.json', 'w') as f:
    json.dump(playlists, f)
