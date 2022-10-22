"""
Description : Getting new songs from my favorite artists.
"""

from datetime import datetime, timedelta
from spotify_module.spotify_class import Spotify
from dotenv import load_dotenv
# from argparse import ArgumentParser, BooleanOptionalAction

# TODO:
# 1. print songs not "albums" in prettytable
# 2. get_tracks_from_albums() -> regroup requests

# load env variables
load_dotenv()

# set important variables
add = True  # add to my spotify's playlists
today_dt = datetime.today().date()
today_str = today_dt.strftime("%Y-%m-%d")
seven_days_ago_str = (today_dt - timedelta(days=6)).strftime("%Y-%m-%d")

# instantiate parser
# parser = ArgumentParser()
# parser.add_argument("-s", "--start", default=seven_days_ago_str, required=False, type=str, metavar="", help="Start date")
# parser.add_argument("-e", "--end", default=today_str, required=False, type=str, metavar="", help="End date")
# parser.add_argument("-a", "--add", action=BooleanOptionalAction, required=False, default=True, help="Add songs to a new playlist")
# args = parser.parse_args()


def run():
    # instantiate Spotify class
    spotify = Spotify()

    artists = spotify.get_favorite_artists()  # get artists I follow
    albums_ids = spotify.get_new_releases(artists, start_date=seven_days_ago_str, end_date=today_str)  # get albums from artists

    # if args.add:  # add to playlist ?
    if add:  # add to playlist ?
        # playlist name
        # start_date = datetime.strptime(seven_days_ago_str, "%Y-%m-%d").strftime('%b %d')
        end_date = datetime.strptime(today_str, "%Y-%m-%d").strftime('%b %d')
        playlist_id = spotify.create_playlist(playlist_name=f'Release Radar ({end_date})')

        # create a playlist
        tracks_uris = spotify.get_tracks_from_albums(albums_ids)

        # add songs to this playlist
        spotify.add_to_playlist(tracks_uris, playlist_id)

        print("Playlist created!")


if __name__ == '__main__':
    run()
