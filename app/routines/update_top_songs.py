"""Update exisiting 'Top songs' playlists."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(ROOT_DIR.as_posix())

from app.config import settings
from app.spotify.client import Spotify
from app.utils import setup_logger, timer

LOGGER = setup_logger("spotify-routines")
# instantiate client
SPOTIFY = Spotify(
    user_id=settings.USER_ID,
    refresh_token=settings.SPOTIFY_REFRESH_TOKEN,
    base64=settings.SPOTIFY_CLIENT_BASE_64,
)


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
def handler(event=None, context=None):
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
    handler()
