"""Update exisiting 'Top songs' playlists."""

import os
from pathlib import Path

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
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN")
CLIENT_BASE_64 = os.environ.get("SPOTIFY_BASE64")
USER_ID = os.environ.get("USER_ID")
# instantiate client
SPOTIFY = Spotify(user_id=USER_ID, refresh_token=REFRESH_TOKEN, base64=CLIENT_BASE_64)


def update_one_playlist(playlist_id: str, artist_name: str):
    # get artist id
    artist_id = SPOTIFY.get_artist_id(name=artist_name)

    # get artist's top albums/songs
    songs_uri = SPOTIFY.get_artist_top_songs(
        artist_id, include="single,album,appears_on"
    )

    # update existing songs' playlist
    SPOTIFY.update_playlist(playlist_id, uris=songs_uri)


@timer(LOGGER)
def main():
    LOGGER.info("Script is running")

    # get artists for which I have a 'Top Songs' playlist
    playlists = SPOTIFY.get_user_playlists(contains="Top Songs")
    # get artist name
    playlists["artist"] = [x.split(":")[0] for x in playlists["name"]]
    # loop trough playlists & update them
    for playlist_id, artist_name in zip(playlists["id"], playlists["artist"]):
        update_one_playlist(playlist_id, artist_name)
        LOGGER.info(f"Updated {artist_name} 'Top Songs' playlist")


if __name__ == "__main__":
    main()
