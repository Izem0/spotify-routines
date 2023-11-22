""" Description : Send email when for releases of new albums (check every friday). """

import os
import sys
from pathlib import Path

import pandas as pd
from spotify.client import Spotify
from dotenv import load_dotenv
from utils import send_email, setup_logger


# TODO: embbed artworks image to email

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs/"
LOGS_DIR.mkdir(exist_ok=True)
LOGGER = setup_logger(
    "spotify",
    log_config_file=BASE_DIR / "logging.yaml",
    log_file=LOGS_DIR / "spotify.log",
)


def main():
    # load env variables
    load_dotenv()

    # set important variables
    end_date = pd.Timestamp.utcnow().date()
    start_date = end_date - pd.Timedelta(days=6)

    # instantiate Spotify class
    refresh_token = os.environ.get("SPOTIFY_REFRESH_TOKEN")
    base64 = os.environ.get("SPOTIFY_BASE64")
    spotify = Spotify(user_id=1181713624, refresh_token=refresh_token, base64=base64)

    # get artists I follow
    LOGGER.info("Getting favorite artists ...")
    df = pd.DataFrame()
    df["artist_id"] = spotify.get_favorite_artists()
    df["artist_name"] = df["artist_id"].apply(spotify.get_artist_name)
    LOGGER.info(f"Found {df.shape[0]} fav. artists.")

    # get albums from those artists
    LOGGER.info("Getting new albums from those artists ...")
    album_ids = []
    for artist_id in df["artist_id"]:
        artist_albums = spotify.get_artist_releases(
            artist_id, start_date=start_date, end_date=end_date, include="album"
        )
        if "id" not in artist_albums.columns:
            album_ids.append([])
        else:
            album_ids.append(artist_albums["id"].to_list())
    df["album_id"] = album_ids
    df = df.explode("album_id").dropna(subset="album_id")

    if df.shape[0] == 0:
        send_email(subject=f"No new albums from your favorite artists")
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
        html=df.to_html(columns=["artist_name", "album_name"], bold_rows=True),
    )
    LOGGER.info(f"Mail sent")


if __name__ == "__main__":
    main()
