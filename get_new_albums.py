""" Description : Send email when for releases of new albums (check every friday). """

import logging
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from spotify_module.spotify_class import Spotify
from dotenv import load_dotenv
from utils import send_email


# TODO: embbed artworks image to email


def main():
    # instantiate log
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO,
                        handlers=[logging.StreamHandler(sys.stdout)])

    # load env variables
    load_dotenv()

    # set important variables
    # add = True  # add to my spotify's playlists
    today_dt = datetime.today().date()
    today_str = today_dt.strftime("%Y-%m-%d")
    seven_days_ago_str = (today_dt - timedelta(days=6)).strftime("%Y-%m-%d")

    # instantiate Spotify class
    refresh_token = os.environ.get("SPOTIFY_REFRESH_TOKEN")
    base64 = os.environ.get("SPOTIFY_BASE64")
    spotify = Spotify(user_id=1181713624, refresh_token=refresh_token, base64=base64)
    
    # get artists I follow
    logging.info('Getting favorite artists ...')
    df = pd.DataFrame()
    df['artist_id'] = spotify.get_favorite_artists()
    df['artist_name'] = df['artist_id'].apply(spotify.get_artist_name)
    logging.info(f"Found {df.shape[0]} fav. artists.")

    # albums from those artists
    logging.info('Getting new albums from those artists ...')
    df['album_id'] = df['artist_id'].apply(
        spotify.get_new_releases,
        start_date=seven_days_ago_str, end_date=today_str, return_='id', include='album'
        )
    df = df.explode('album_id').dropna(subset='album_id')
    df['album_name'] = df['album_id'].apply(lambda x: spotify.get_album(x)['name'])
    df.drop_duplicates(subset=['artist_name', 'album_name'], inplace=True)

    # like those albums
    spotify.save_albums(ids=df['album_id'].to_list())

    # send email
    n_albums = len(df['album_id'].unique())
    send_email(subject=f'{n_albums} new albums found from your favorite artists!',
               html=df.to_html(columns=['artist_name', 'album_name'], bold_rows=True))


if __name__ == '__main__':
    main()
