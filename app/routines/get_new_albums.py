"""Send myself an email if my favorites artists released a new album in the past week (to run every friday)."""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(ROOT_DIR.as_posix())

import pandas as pd

from app.config import settings
from app.spotify.client import Spotify
from app.utils import send_email, setup_logger, timer

LOGGER = setup_logger("spotify-routines")
END_DATE = pd.Timestamp.utcnow().date()
START_DATE = END_DATE - pd.Timedelta(days=6)


@timer(LOGGER)
def handler(event=None, context=None):
    # instantiate class
    spotify = Spotify(
        user_id=settings.USER_ID,
        refresh_token=settings.SPOTIFY_REFRESH_TOKEN,
        base64=settings.SPOTIFY_CLIENT_BASE_64,
    )

    # get artists I follow
    LOGGER.info("Getting favorite artists...")
    df = pd.DataFrame()
    df["artist_id"] = spotify.get_favorite_artists()
    df["artist_name"] = df["artist_id"].apply(spotify.get_artist_name)
    LOGGER.info(f"Found {df.shape[0]} fav. artists.")

    # get albums from those artists
    LOGGER.info("Getting new albums from those artists...")
    album_ids = []
    for artist_id in df["artist_id"]:
        artist_albums = spotify.get_artist_releases(
            artist_id, start_date=START_DATE, end_date=END_DATE, include="album"
        )
        if "id" not in artist_albums.columns:
            album_ids.append([])
        else:
            album_ids.append(artist_albums["id"].to_list())
    df["album_id"] = album_ids
    df = df.explode("album_id").dropna(subset="album_id")

    if df.empty:
        msg = "No new albums from your favorite artists"
        LOGGER.info(msg)
        send_email(
            sender=settings.GMAIL_ADDRESS,
            receipient=settings.GMAIL_ADDRESS,
            subject=msg,
        )
        return

    df["album_name"] = df["album_id"].apply(lambda x: spotify.get_album(x)["name"])
    df.drop_duplicates(subset=["artist_name", "album_name"], inplace=True)
    n_albums = len(df["album_id"].unique())
    LOGGER.info(f"Found {n_albums} albums")

    # like those albums
    spotify.save_albums(ids=df["album_id"].to_list())
    LOGGER.info(f"{n_albums} albums liked")

    # send email
    send_email(
        subject=f"{n_albums} new albums found from your favorite artists!",
        html=df.to_html(
            columns=["artist_name", "album_name"], bold_rows=True, index=False
        ),
    )
    LOGGER.info(f"Mail sent.")


if __name__ == "__main__":
    handler()
