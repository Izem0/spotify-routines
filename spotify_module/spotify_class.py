import requests
import json
import pandas as pd
from spotify_module.refresh import Refresh


class Spotify:
    def __init__(self, user_id, refresh_token, base64):
        self.user_id = user_id
        refresh = Refresh(refresh_token, base64)
        self.spotify_token = refresh.refresh()
        self.headers = {"Accept": "application/json",
                        "Content-type": "application/json",
                        "Authorization": f"Bearer {self.spotify_token}"}

    def get_favorite_artists(self) -> list[str]:
        """Get ids of the artists I follow
        https://developer.spotify.com/documentation/web-api/reference/#/operations/get-followed"""

        end_point = 'https://api.spotify.com/v1/me/following'

        # loop to get all artists id (limit: 50 artists per request)
        artists = []
        after = None
        while True:
            params = {'type': 'artist', 'after': after, 'limit': '50'}
            r = requests.get(end_point, headers=self.headers, params=params)

            for item in r.json()['artists']['items']:
                artists.append(item['id'])

            after = r.json()['artists']['cursors'].get('after')
            if after is None:
                break

        return artists

    def get_artist_name(self, artist_id: str):
        end_point = f"https://api.spotify.com/v1/artists/{artist_id}"
        r = requests.get(end_point, headers=self.headers)
        return r.json()['name']

    def get_new_releases(self, artist_id: str, start_date='', end_date='', return_='id', include='album,single,appears_on'):
        """ Get artist's new releases (uris)
        Inlude album_groups: 'album,single,appears_on' or 'album,single' ..."""
        # if artist_id != '2QVJnfY0oreRfL5HOnbBgy':
        #     return []
        # print(self.get_artist_name(artist_id))

        end_point = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
        params = {'country': 'FR', 'limit': '50', "include_groups": include}
        response = requests.get(end_point, headers=self.headers, params=params)
        rjson = response.json()

        df = pd.DataFrame(rjson['items'])

        if df.shape[0] > 0:
            df['various_artists'] = df['artists'].apply(lambda x: x[0]['name'] == 'Various Artists')
            df = df.query(f"release_date >= '{start_date}' and release_date <= '{end_date}' and album_type != 'compilation' and various_artists == False")

        return df[return_].to_list()

    def get_album(self, album_id: str) -> dict:
        url = f'https://api.spotify.com/v1/albums/{album_id}'
        r = requests.get(url, headers=self.headers)
        return r.json()

    # def get_album_name(self, album_id: str) -> dict:
    #     url = f'https://api.spotify.com/v1/albums/{album_id}'
    #     r = requests.get(url, headers=self.headers)
    #     return r.json()['name']

    def get_tracks_from_album(self, album_id: str, return_names: bool = False) -> pd.DataFrame:
        """Return tracks from a given album id"""

        end_point = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
        r = requests.get(end_point, headers=self.headers, params={"market": "FR", "limit": "50"})
        rjson = r.json()

        if return_names:
            return pd.DataFrame(rjson['items'])['name'].to_list()

        return pd.DataFrame(rjson['items'])

    def get_devices(self):

        end_point = "https://api.spotify.com/v1/me/player/devices"
        response = requests.get(end_point, headers=self.headers)
        response_json = response.json()
        devices = response_json["devices"]

        return devices

    def add_to_queue(self, tracks_uris, device_id):

        # request
        end_point = "https://api.spotify.com/v1/me/player/queue"
        for track_uri in tracks_uris:          # loop through tracks
            params = {"uri": f"{track_uri}", "device_id": f"{device_id}"}
            requests.post(end_point, headers=self.headers, params=params)

    def create_playlist(self, playlist_name):
        end_point = f"https://api.spotify.com/v1/users/{self.user_id}/playlists"
        data = {'name': playlist_name,
                "public": "false"}
        response = requests.post(end_point, headers=self.headers, data=json.dumps(data))
        response_json = response.json()

        return response_json["id"]

    def get_songs_from_playlist(self, paylist_id: str, return_: str = 'name') -> list[str]:
        """Return tracks 'uri' or 'name' from a given playlist"""
        # request
        end_point = f"https://api.spotify.com/v1/playlists/{paylist_id}/tracks"
        r = requests.get(end_point, headers=self.headers)
        rjson = r.json()

        # parse track names
        release_radar_tracks = [item["track"]["album"].get(return_) for item in rjson["items"]
                                if item["track"] is not None]
        return release_radar_tracks

    def update_playlist_items(self, playlist_id: str, tracks_uris: list[str]) -> None:
        """Either reorder or replace items in a playlist depending on the request's parameters.
        https://developer.spotify.com/documentation/web-api/reference/#/operations/reorder-or-replace-playlists-tracks"""
        # make a long string of tracks uris
        tracks_uris_list = ','.join(tracks_uris)

        # request
        end_point = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        params = {"uris": tracks_uris_list}
        requests.put(end_point, headers=self.headers, params=params)

    def get_user_playlists(self, contains: str = None):
        params = {'limit': 30, 'offset': 0}
        url = 'https://api.spotify.com/v1/me/playlists'
        ls = []
        while True:
            r = requests.get(url, headers=self.headers, params=params)
            if not r.json()['items']:
                break

            ls.extend(r.json()['items'])
            params['offset'] += params['limit']

        df = pd.DataFrame(ls)
        if contains is not None:
            df = df.query(f"name.str.contains('{contains}')")

        return df

    def update_playlist_details(self, playlist_id: int, name: str = 'New Playlist', public: bool = False, collaborative: bool = False, description: str = 'Issa description.') -> None:
        """Change a playlist's name and public/private state (the user must, of course, own the playlist).
        https://developer.spotify.com/documentation/web-api/reference/#/operations/change-playlist-details"""
        data = {'name': name, 'public': public, 'collaborative': collaborative, 'description': description}
        url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
        r = requests.put(url, data=json.dumps(data), headers=self.headers)
