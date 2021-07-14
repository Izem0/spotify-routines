"""
Date    : May, 2021
Author  : Izem Mangione
Email   : izem.mangione@gmail.com
File    : main.py
Software: PyCharm

Description :
"""
import argparse
from spotify_module.spotify_class import Spotify

"""
TO DO: 
1. print songs not "albums" in prettytable
2. get_tracks_from_albums() -> regroup requests
"""

# instantiate parser
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--days", default=7, required=False, type=int, metavar="", help="Number of days ago")
parser.add_argument("-a", "--add", action="store_true", default=False, help="Add songs to queue")
args = parser.parse_args()

# instantiate Spotify class
spotify = Spotify()

artists = spotify.get_favorite_artists()  # get artists I follow
albums_ids = spotify.get_new_releases(artists, n_days=args.days)  # get albums from artists
# add to queue?
if args.add:
    tracks_uris = spotify.get_tracks_from_albums(albums_ids)  # get tracks from those albums
    devices = spotify.get_devices()
    spotify.add_to_queue(tracks_uris, devices[0]["id"])  # add those tracks to playing queue :)
