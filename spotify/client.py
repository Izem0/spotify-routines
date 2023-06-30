import requests
import pandas as pd
from .refresh import Refresh


class Spotify:
    _BASE_URL = 'https://api.spotify.com/v1/'

    def __init__(self, user_id, refresh_token, base64):
        self.user_id = user_id
        refresh = Refresh(refresh_token, base64)
        self.spotify_token = refresh.refresh()
        self.headers = {"Accept": "application/json",
                        "Content-type": "application/json",
                        "Authorization": f"Bearer {self.spotify_token}"}
        
    # =========== Request methods =========== #
    def _get(self, endpoint, params=[], **kwargs):
        r = requests.get(self._BASE_URL + endpoint, params=params, headers=self.headers, **kwargs)
        return r

    def _put(self, endpoint, data=[], params=[], **kwargs):
        r = requests.put(self._BASE_URL + endpoint, data=data, params=params, headers=self.headers, **kwargs)
        return r
    
    def _post(self, endpoint, data=[], json=[], **kwargs):
        r = requests.post(self._BASE_URL + endpoint, data=data, json=json, headers=self.headers, **kwargs)
        return r

    # =========== Endpoints =========== #
    def get_favorite_artists(self, return_: str = 'id') -> list[str]:
        """CUSTOM. Get ids of the artists I follow.
        :return_: Can be one in ['id', 'name']
        https://developer.spotify.com/documentation/web-api/reference/#/operations/get-followed"""

        # loop to get all artists id (limit: 50 artists per request)
        artists = []
        after = None
        while True:
            params = {'type': 'artist', 'after': after, 'limit': '50'}
            r = self._get('me/following', params=params)

            for item in r.json()['artists']['items']:
                artists.append(item.get(return_))

            after = r.json()['artists']['cursors'].get('after')
            if after is None:
                break

        return artists

    def get_artist_name(self, artist_id: str) -> str:
        r = self._get(f"artists/{artist_id}")
        return r.json()['name']

    def get_artist_releases(
            self,
            artist_id: str,
            start_date=(pd.Timestamp.utcnow() - pd.Timedelta(days=7)).date(),
            end_date=pd.Timestamp.utcnow().date(),
            include='album,single,appears_on',
            limit=50,
            market='FR',
            offset=0
            ) -> list[str]:
        """Get artist's new releases (uris)
        Include album_groups: 'album,single,appears_on,compilation' or 'album,single' ..."""
       
        params = {'market': market, 'limit': limit, 'include_groups': include, 'offset': offset}
        r = self._get(f"artists/{artist_id}/albums", params=params)
        df = pd.DataFrame(r.json()['items'])

        if df.shape[0] > 0:
            df['various_artists'] = df['artists'].apply(lambda x: x[0]['name'] == 'Various Artists')  # flag 'various artists' albums
            df = df.query(f"release_date >= '{start_date.isoformat()}' and release_date <= '{end_date.isoformat()}' and album_type != 'compilation' and various_artists == False")

        return df

    def get_album(self, album_id: str, market: str = 'FR') -> dict:
        """Get Spotify catalog information for a single album.
        https://developer.spotify.com/documentation/web-api/reference/#/operations/get-an-album"""
        params = {'market': market}
        r = self._get(f"albums/{album_id}", params=params)
        return r.json()

    def get_tracks_from_album(self, album_id: str, limit: int = 50, market: str = 'FR', offset: int = 0) -> pd.DataFrame:
        """Return tracks from a given album id
        https://developer.spotify.com/documentation/web-api/reference/#/operations/get-an-albums-tracks"""
        params = {'limit': limit, 'market': market, 'offset': offset}
        r = self._get(f"albums/{album_id}/tracks", params=params)
        return pd.DataFrame(r.json()['items'])

    def get_devices(self) -> dict:
        r = self._get("me/player/devices")
        return r.json()

    def add_to_queue(self, tracks_uris: list[str], device_id: str):
        """Add an item to the end of the user's current playback queue.
        https://developer.spotify.com/documentation/web-api/reference/#/operations/add-to-queue"""
        for track_uri in tracks_uris:  # loop through tracks
            data = {"uri": track_uri, "device_id": device_id}
            self._post("me/player/queue", json=data)

    def create_playlist(self, name: str = 'New Playlist', public: bool = False, collaborative: bool = False, description: str = 'Issa description.'):
        """Create a playlist for a Spotify user. (The playlist will be empty until you add tracks.)
        https://developer.spotify.com/documentation/web-api/reference/#/operations/create-playlist"""
        data = {'name': name, 'public': public, 'collaborative': collaborative, 'description': description}
        r = self._post(f"users/{self.user_id}/playlists", json=data)
        return r
    
    def update_playlist_details(self, playlist_id: int, name: str = 'New Playlist', public: bool = False, collaborative: bool = False, description: str = 'Issa description.') -> None:
        """Change a playlist's name and public/private state (the user must, of course, own the playlist).
        https://developer.spotify.com/documentation/web-api/reference/#/operations/change-playlist-details"""
        data = {'name': name, 'public': public, 'collaborative': collaborative, 'description': description}
        r = self._put(f"playlists/{playlist_id}", json=data)
        return r

    def get_songs_from_playlist(self, paylist_id: str) -> pd.DataFrame:
        """Get full details of the items of a playlist owned by a Spotify user.
        https://developer.spotify.com/documentation/web-api/reference/#/operations/get-playlists-tracks"""
        r = self._get(f"playlists/{paylist_id}/tracks")
        # parse track names
        # songs = [item["track"]["album"].get(return_) for item in r.json()["items"]
        #                         if item["track"] is not None]
        # return pd.DataFrame([x['track'] for x in r.json()['items']])
        return pd.json_normalize([x['track'] for x in r.json()['items']])
    
    def update_playlist_items(self, playlist_id: str, tracks_uris: list[str]) -> None:
        """Either reorder or replace items in a playlist depending on the request's parameters.
        https://developer.spotify.com/documentation/web-api/reference/#/operations/reorder-or-replace-playlists-tracks"""
        data = {'uris': tracks_uris}
        r = self._put(f"playlists/{playlist_id}/tracks", json=data)
        return r

    def get_user_playlists(self, contains: str = None) -> pd.DataFrame:
        params = {'limit': 30, 'offset': 0}
        ls = []
        while True:
            r = self._get('me/playlists', params=params)
            if not r.json()['items']:
                break

            ls.extend(r.json()['items'])
            params['offset'] += params['limit']

        df = pd.DataFrame(ls)
        if contains is not None:
            df = df.query(f"name.str.contains('{contains}')")

        return df

    def save_albums(self, ids: list[str]) -> None:
        """Save one or more albums to the current user's 'Your Music' library.

        ids: str
        A comma-separated list of the Spotify IDs for the albums. Maximum: 20 IDs.
        Example value:
        "382ObEPsp2rxGrnsizN5TX,1A2GTWGtFfWp7KSQTwWOyo,2noRn2Aes5aoNVsU6iWThc"

        https://developer.spotify.com/documentation/web-api/reference/#/operations/save-albums-user
        """
        r = self._put('me/albums', json=ids)
        return r
