"""Get new songs from my favorite artists and add them to a playlist"""

import os
from pathlib import Path

import pandas as pd
from spotify.client import Spotify
from dotenv import load_dotenv
from infisical import InfisicalClient
from utils import setup_logger

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
RELEASE_RADAR_ID = os.environ.get("RELEASE_RADAR_ID")


def main():
    # instantiate class
    spotify = Spotify(user_id=USER_ID, refresh_token=REFRESH_TOKEN, base64=CLIENT_BASE_64)

    # first get previous playlist id
    my_playlists = spotify.get_user_playlists()
    my_playlists['cus_release_radar'] = my_playlists['name'].str.contains('Release Radar \(\S+\s\d+\)', regex=True)
    if my_playlists['cus_release_radar'].sum() > 1:
        raise Exception("There a more than 1 custom Release Radar playlists! Need only one.")
    elif my_playlists['cus_release_radar'].sum() == 0:
        raise Exception("No already existing custom Release Radar playlists! Need one.")
    playlist_id = my_playlists.query("cus_release_radar == True")['id'].iloc[0]

    # get artists I follow
    LOGGER.info('Getting favorite artists ...')
    artists = spotify.get_favorite_artists()
    LOGGER.info(f"Found {len(artists)} fav. artists.")

    # get new releases from those artists
    LOGGER.info('Getting new albums from those artists ...')
    new_albums = pd.DataFrame()
    for artist_id in artists:
    # for artist_id in ['3TVXtAsR1Inumwj472S9r4']:  # debug
        new_albums = pd.concat(
            [new_albums, spotify.get_artist_releases(artist_id, start_date=START_DATE, end_date=END_DATE)[["id", 'name']]],
            ignore_index=True
        )

    # get songs from release radar to not add them
    LOGGER.info('Getting songs from release radar ...')
    radar_albums = spotify.get_songs_from_playlist(RELEASE_RADAR_ID)[["id", 'name']]

    # songs that are in new_releases but not in radar_albums
    merge = new_albums.merge(radar_albums, on='name', how='left', indicator=True)
    merge = merge.query("_merge == 'left_only'").drop_duplicates(subset=['name'], keep='first')

    # get tracks uris from albums
    tracks = pd.DataFrame()
    for album in merge['id_x'].to_list():
        tracks = pd.concat([tracks, spotify.get_tracks_from_album(album)])
    tracks.drop_duplicates('name', keep='first', inplace=True)  # remove non explicit
    tracks = tracks.explode('artists')
    tracks['artist_name'] = [x['name'] for x in tracks['artists']]
    artists_names = [spotify.get_artist_name(id_) for id_ in artists]
    tracks = tracks.query(f"artist_name.isin({artists_names})").drop_duplicates('uri')
    tracks_uris = tracks['uri'].to_list()

    # update playlist description
    LOGGER.info('Updating playlist ...')
    playlist_name = f"Release Radar ({END_DATE.strftime('%b %d')})"
    spotify.update_playlist_details(playlist_id, name=playlist_name)

    # update playlist with new songs
    LOGGER.info(f'Add songs to to playlist {playlist_name} ...')
    spotify.update_playlist_items(playlist_id, tracks_uris)


if __name__ == '__main__':
    main()
