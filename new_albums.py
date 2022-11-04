"""
Description : Send email when for releases of new albums (check every friday).
"""
import logging
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from spotify_module.spotify_class import Spotify
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage


# TODO: embbed artworks image to email

def send_email(sender="izem.mangione@gmail.com", receipient="izem.mangione@gmail.com",
               subject='', body='', html=None):

    msg = EmailMessage()

    # generic email headers
    msg["From"] = sender
    msg["To"] = receipient
    msg["Subject"] = subject

    # set the body of the mail
    msg.set_content(body)

    if html:
        msg.add_alternative(html, subtype='html')

    # send it using smtplib
    email_address = os.getenv("GMAIL_ADDRESS")
    email_password = os.getenv("GMAIL_PASSWORD")
    with smtplib.SMTP_SSL("smtp.gmail.com", 0) as smtp:
        smtp.login(email_address, email_password)
        smtp.send_message(msg)

    logging.info(f"Mail sent to {receipient}.")


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


def run():
    # instantiate Spotify class
    spotify = Spotify()
    df = pd.DataFrame()

    # get artists I follow
    logging.info('Getting favorite artists ...')
    df['artist_id'] = spotify.get_favorite_artists()
    df['artist_name'] = df['artist_id'].apply(spotify.get_artist_name)
    logging.info(f"Found {df.shape[0]} fav. artists.")

    # albums from those artists
    logging.info('Getting new albums from those artists ...')
    df['album_id'] = df['artist_id'].apply(spotify.get_new_releases, start_date=seven_days_ago_str, end_date=today_str, return_='id', include='album')
    df = df.explode('album_id').dropna(subset='album_id')
    df['album_name'] = df['album_id'].apply(lambda x: spotify.get_album(x)['name'])

    # get tracks from albums
    df['track'] = df['album_id'].apply(spotify.get_tracks_from_album, return_names=True)
    df = df.explode('track')

    df.set_index(['artist_name', 'album_name'], inplace=True)

    n_albums = len(df['album_id'].unique())
    send_email(subject=f'{n_albums} albums found from your favorite artists!',
               html=df.to_html(columns=['track'], bold_rows=True))


if __name__ == '__main__':
    run()
