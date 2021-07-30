"""
Date    : May, 2021
Author  : Izem Mangione
Email   : izem.mangione@gmail.com
File    : main.py
Software: PyCharm

Description :
"""
import argparse
from datetime import datetime
from spotify_module.spotify_class import Spotify

"""
TO DO: 
1. print songs not "albums" in prettytable
2. get_tracks_from_albums() -> regroup requests
"""

# instantiate parser
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--days", default=6, required=False, type=int, metavar="", help="Number of days ago")
parser.add_argument("-a", "--add", action="store_true", default=False, help="Add songs to a new playlist")
args = parser.parse_args()

# instantiate Spotify class
spotify = Spotify()

artists = spotify.get_favorite_artists()  # get artists I follow
albums_ids = spotify.get_new_releases(artists, n_days=args.days)  # get albums from artists

if args.add:  # add to playlist ?
    # playlist name
    today_date = datetime.today().date().strftime("%B, %d")
    playlist_id = spotify.create_playlist(playlist_name=f'Release Radar ({today_date})')

    tracks_uris = spotify.get_tracks_from_albums(albums_ids)  # create a playlist
    spotify.add_to_playlist(tracks_uris, playlist_id)  # add songs to this playlist
