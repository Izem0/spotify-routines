"""Create a 'Top Songs' playlist with the top N most popular songs of a given artist."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(ROOT_DIR.as_posix())

import pandas as pd

from app.config import settings
from app.spotify.client import Spotify
from app.utils import setup_logger, timer

LOGGER = setup_logger("spotify-routines")
END_DATE = pd.Timestamp.utcnow().date()
START_DATE = END_DATE - pd.Timedelta(days=6)


def create_this_is_playlist(artist_name: str, n_tracks: int = 50):
    # instantiate class
    spotify = Spotify(
        user_id=settings.USER_ID,
        refresh_token=settings.SPOTIFY_REFRESH_TOKEN,
        base64=settings.SPOTIFY_CLIENT_BASE_64,
    )

    # get artist id
    artist_id = spotify.get_artist_id(name=artist_name)

    # get albums/songs from the artist
    songs_uri = spotify.get_artist_top_songs(
        artist_id, n=n_tracks, include="single,album,appears_on"
    )

    # create the playlist
    playlist_id = spotify.create_playlist(
        name=f"{artist_name}: Top Songs",
        description=f"Top songs of {artist_name}, ordered by popularity from highest to lowest. "
        f"This playlist is updated every friday at 00:00:00 UTC.",
    )

    # add songs to the playlist
    spotify.add_to_playlist(playlist_id, tracks_uris=songs_uri)
    LOGGER.info(f"Playlist created for {artist_name}")


@timer(LOGGER)
def main():
    artists = ["GLK"]
    for artist in artists:
        create_this_is_playlist(artist_name=artist)


if __name__ == "__main__":
    main()
