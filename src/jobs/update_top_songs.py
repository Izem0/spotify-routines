"""Update exisiting 'Top songs' playlists"""

import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1].as_posix()
sys.path.append(ROOT_DIR)

from config import settings  # noqa: E402
from lib.client import Spotify  # noqa: E402
from lib.logger import setup_logger  # noqa: E402
from lib.timer import timer  # noqa: E402

LOGGER = setup_logger("spotify-routines")


def update_one_playlist(spotify: Spotify, playlist_id: str, artist_name: str):
    # get artist id
    artist_id = spotify.get_artist_id(name=artist_name)

    # get artist's top albums/songs
    songs_uri = spotify.get_artist_top_songs(
        artist_id, include="single,album,appears_on"
    )

    # update existing songs' playlist
    spotify.update_playlist(playlist_id, uris=songs_uri)

    # update playlist's details
    desc = (
        f"Top songs of {artist_name}, "
        "ordered by popularity from highest to lowest. "
        f"Last update: {datetime.now().strftime('%Y-%m-%d')}"
    )
    spotify.change_playlist_details(playlist_id, description=desc)

    return artist_name


@timer(LOGGER)
def main() -> None:
    LOGGER.info("Script is running")

    # instantiate client
    spotify = Spotify(
        user_id=settings.USER_ID,
        refresh_token=settings.SPOTIFY_REFRESH_TOKEN,
        base64=settings.SPOTIFY_CLIENT_BASE_64,
    )
    # get artists for which I have a 'Top Songs' playlist
    playlists = spotify.get_user_playlists(regex=".*?: Top Songs")

    # get artists names
    playlists["artist"] = [x.split(":")[0] for x in playlists["name"]]

    # loop trough playlists & update them
    for playlist_id, artist_name in zip(playlists["id"], playlists["artist"]):
        update_one_playlist(spotify, playlist_id, artist_name)
        LOGGER.info(f"Updated {artist_name} 'Top Songs' playlist")


if __name__ == "__main__":
    main()
