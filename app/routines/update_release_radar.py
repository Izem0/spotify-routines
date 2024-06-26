"""Get new songs from my favorite artists and update custom 'Release Radar' playlist"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(ROOT_DIR.as_posix())

import pandas as pd

from app.config import settings
from app.spotify.client import Spotify
from app.utils import setup_logger, timer

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

    # first get previous playlist id
    my_playlists = spotify.get_user_playlists()
    my_playlists["cus_release_radar"] = my_playlists["name"].str.contains(
        r"Release Radar \(\S+\s\d+\)", regex=True
    )
    if my_playlists["cus_release_radar"].sum() > 1:
        raise Exception(
            "There a more than 1 custom Release Radar playlists! Need only one."
        )
    elif my_playlists["cus_release_radar"].sum() == 0:
        raise Exception("No already existing custom Release Radar playlists! Need one.")
    playlist_id = my_playlists.query("cus_release_radar == True")["id"].iloc[0]

    # get artists I follow
    LOGGER.info("Getting favorite artists ...")
    artists = spotify.get_favorite_artists()
    LOGGER.info(f"Found {len(artists)} fav. artists.")

    # get new releases from those artists
    LOGGER.info("Getting new albums from those artists ...")
    new_albums = pd.DataFrame()
    for artist_id in artists:
        # for artist_id in ['3TVXtAsR1Inumwj472S9r4']:  # debug
        new_albums = pd.concat(
            [
                new_albums,
                spotify.get_artist_releases(
                    artist_id, start_date=START_DATE, end_date=END_DATE
                )[["id", "name"]],
            ],
            ignore_index=True,
        )

    # get songs from release radar to not add them
    LOGGER.info("Getting songs from release radar ...")
    radar_albums = spotify.get_songs_from_playlist(settings.RELEASE_RADAR_ID)[
        ["id", "name"]
    ]

    # songs that are in new_releases but not in radar_albums
    merge = new_albums.merge(radar_albums, on="name", how="left", indicator=True)
    merge = merge.query("_merge == 'left_only'").drop_duplicates(
        subset=["name"], keep="first"
    )

    # get tracks uris from albums
    tracks = pd.DataFrame()
    for album in merge["id_x"].to_list():
        tracks = pd.concat([tracks, spotify.get_tracks_from_album(album)])
    tracks.drop_duplicates("name", keep="first", inplace=True)  # remove non explicit
    tracks = tracks.explode("artists")
    tracks["artist_name"] = [x["name"] for x in tracks["artists"]]
    artists_names = [spotify.get_artist_name(id_) for id_ in artists]
    tracks = tracks.query(f"artist_name.isin({artists_names})").drop_duplicates("uri")
    tracks_uris = tracks["uri"].to_list()

    # update playlist description
    LOGGER.info("Updating playlist ...")
    playlist_name = f"Release Radar ({END_DATE.strftime('%b %d')})"
    spotify.change_playlist_details(playlist_id, name=playlist_name)

    # update playlist with new songs
    LOGGER.info(f"Add songs to to playlist {playlist_name} ...")
    spotify.update_playlist_items(playlist_id, tracks_uris)


if __name__ == "__main__":
    handler()
