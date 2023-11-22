"""Send myself an email when my favorites artists released a new song/album (check every friday)."""

import os
from pathlib import Path

import pandas as pd
from spotify.client import Spotify
from dotenv import load_dotenv
from infisical import InfisicalClient
from utils import send_email, setup_logger

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


def main():
    # instantiate class
    spotify = Spotify(user_id=USER_ID, refresh_token=REFRESH_TOKEN, base64=CLIENT_BASE_64)

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
    LOGGER.info(f"Mail sent.")


if __name__ == "__main__":
    main()
