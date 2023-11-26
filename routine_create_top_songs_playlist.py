"""Create a 'Top Songs' playlist with the top N most popular songs of a given artist."""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from infisical import InfisicalClient

from spotify.client import Spotify
from utils import setup_logger, timer

# load env. variables
load_dotenv()
infisical = InfisicalClient(token=os.getenv("INFISICAL_TOKEN"))
infisical.get_all_secrets(attach_to_os_environ=True)


BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs/"
LOGS_DIR.mkdir(exist_ok=True)
LOGGER = setup_logger(
    "spotify",
    log_config_file=BASE_DIR / "logging.yaml",
    log_file=LOGS_DIR / "spotify.log",
)
END_DATE = pd.Timestamp.utcnow().date()
START_DATE = END_DATE - pd.Timedelta(days=6)
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN")
CLIENT_BASE_64 = os.environ.get("SPOTIFY_BASE64")
USER_ID = os.environ.get("USER_ID")


def create_this_is_playlist(artist_name: str, n_tracks: int = 50):
    # instantiate class
    spotify = Spotify(
        user_id=USER_ID, refresh_token=REFRESH_TOKEN, base64=CLIENT_BASE_64
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
    artists = ["Taylor Swift"]
    for artist in artists:
        create_this_is_playlist(artist_name=artist)


if __name__ == "__main__":
    main()
