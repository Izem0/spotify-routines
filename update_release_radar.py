"""Get new songs from my favorite artists and add them to a playlist"""

import logging
import sys
import time
import os
import pandas as pd
from spotify.client import Spotify
from dotenv import load_dotenv

# TODO:
#   - 'difference of release new songs & radar songs' -> do it with title name, not ids
#   - get_tracks_from_albums() -> regroup requests
#   - don't include albums (see get_new_releases())
#   - create playlist if none exist

def main():
    # timer
    t1 = time.perf_counter()

    # instantiate log
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO,
                        handlers=[logging.StreamHandler(sys.stdout)])

    # load env variables
    load_dotenv()

    # set important variables
    release_radar_id = "37i9dQZEVXbkf1UTJ14JFi"
    end_date = pd.Timestamp.utcnow().date()
    start_date = end_date - pd.Timedelta(days=6)

    # instantiate Spotify class
    refresh_token = os.environ.get("SPOTIFY_REFRESH_TOKEN")
    base64 = os.environ.get("SPOTIFY_BASE64")
    spotify = Spotify(user_id=1181713624, refresh_token=refresh_token, base64=base64)

    # first get previous playlist id
    my_playlists = spotify.get_user_playlists()
    my_playlists['cus_release_radar'] = my_playlists['name'].str.contains('Release Radar \(\S+\s\d+\)', regex=True)
    if my_playlists['cus_release_radar'].sum() > 1:
        raise Exception("There a more than 1 custom Release Radar playlists! Need only one.")
    elif my_playlists['cus_release_radar'].sum() == 0:
        raise Exception("No already existing custom Release Radar playlists! Need one.")
    playlist_id = my_playlists.query("cus_release_radar == True")['id'].iloc[0]

    # get artists I follow
    logging.info('Getting favorite artists ...')
    artists = spotify.get_favorite_artists()
    logging.info(f"Found {len(artists)} fav. artists.")

    # get new releases from those artists
    logging.info('Getting new albums from those artists ...')
    albums_ids = []
    for artist_id in artists:
    # for artist_id in ['3TVXtAsR1Inumwj472S9r4']:  # debug
        new_release = spotify.get_artist_releases(artist_id, start_date=start_date, end_date=end_date)
        albums_ids.extend(new_release)

    # get songs from release radar to not add them
    logging.info('Getting songs from release radar ...')
    radar_albums_ids = spotify.get_songs_from_playlist(release_radar_id, return_='id')

    # difference of release new songs & radar songs
    diff = list(set(albums_ids) - set(radar_albums_ids))

    # get tracks uris from albums
    tracks = pd.DataFrame()
    for album in diff:
        tracks = pd.concat([tracks, spotify.get_tracks_from_album(album)])
    tracks.drop_duplicates('name', keep='first', inplace=True)  # remove non explicit
    tracks = tracks.explode('artists')
    tracks['artist_name'] = [x['name'] for x in tracks['artists']]
    artists_names = [spotify.get_artist_name(id_) for id_ in artists]
    tracks = tracks.query(f"artist_name.isin({artists_names})").drop_duplicates('uri')
    tracks_uris = tracks['uri'].to_list()

    # update playlist description
    logging.info('Updating playlist ...')
    playlist_name = f"Release Radar ({end_date.strftime('%b %d')})"
    spotify.update_playlist_details(playlist_id, name=playlist_name)

    # update playlist with new songs
    logging.info(f'Add songs to to playlist {playlist_name} ...')
    spotify.update_playlist_items(playlist_id, tracks_uris)

    # finish
    t2 = time.perf_counter()
    logging.info(f"Done. Elapsed time: {str(pd.Timedelta(seconds=t2-t1))[:-10]}")


if __name__ == '__main__':
    main()
