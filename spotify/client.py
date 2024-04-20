from datetime import date

import backoff
import pandas as pd
import requests

from spotify.refresh import Refresh
from spotify.utils import backoff_hdlr, remove_nones, n_chunks


class Spotify:
    _BASE_URL = "https://api.spotify.com/v1/"

    def __init__(self, user_id, refresh_token, base64):
        self.user_id = user_id
        refresh = Refresh(refresh_token, base64)
        self.spotify_token = refresh.refresh()
        self.headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
            "Authorization": f"Bearer {self.spotify_token}",
        }

    ###################
    # REQUEST METHODS #
    ###################
    @backoff.on_predicate(
        backoff.expo,
        predicate=lambda r: 400 <= r.status_code < 500,
        max_time=300,
        on_backoff=backoff_hdlr,
    )
    def _get(self, endpoint, params=[], **kwargs):
        r = requests.get(
            self._BASE_URL + endpoint, params=params, headers=self.headers, **kwargs
        )
        return r

    def _put(self, endpoint, data=[], params=[], **kwargs):
        r = requests.put(
            self._BASE_URL + endpoint,
            data=data,
            params=params,
            headers=self.headers,
            **kwargs,
        )
        return r

    def _post(self, endpoint, data=[], json=[], **kwargs):
        r = requests.post(
            self._BASE_URL + endpoint,
            data=data,
            json=json,
            headers=self.headers,
            **kwargs,
        )
        return r

    #############
    # ENDPOINTS #
    #############
    def get_favorite_artists(self, return_: str = "id", type: str = "artist") -> list[str]:
        """Get ids/name of the artists I follow.
        :return_: Can be one in ['id', 'name']
        Adapted from https://developer.spotify.com/documentation/web-api/reference/#/operations/get-followed"""
        if return_ not in ['id', 'name']:
            raise ValueError(f"'return_' parameter should be one of ['id', 'name'].")
        # loop to get all artists id (limit: 50 artists per request)
        artists = []
        after = None
        while True:
            params = {"type": type, "after": after, "limit": "50"}
            r = self._get("me/following", params=params)

            for item in r.json()["artists"]["items"]:
                artists.append(item.get(return_))

            after = r.json()["artists"]["cursors"].get("after")
            if after is None:
                break

        return artists

    def get_artist_name(self, artist_id: str) -> str:
        """Get artist's name given their id."""
        r = self._get(f"artists/{artist_id}")
        return r.json()["name"]

    def get_artist_releases(
        self,
        artist_id: str,
        start_date: date = None,
        end_date: date = None,
        include: str = "album,single,appears_on",
        market: str = "FR",
        limit: str = 50,
        offset: str = 0,
    ) -> pd.DataFrame:
        """Get artist's new releases.
        Adapted from https://developer.spotify.com/documentation/web-api/reference/get-an-artists-albums"""
        if start_date is None:
            start_date = (pd.Timestamp.utcnow() - pd.Timedelta(days=7)).date()
        if end_date is None:
            end_date = pd.Timestamp.utcnow().date(),
        
        params = {
            "market": market,
            "limit": limit,
            "include_groups": include,
            "offset": offset,
        }
        r = self._get(f"artists/{artist_id}/albums", params=params)
        df = pd.DataFrame(r.json()["items"])

        if df.empty:
            return df
        
        df["various_artists"] = df["artists"].apply(
            lambda x: x[0]["name"] == "Various Artists"
        )  # flag 'various artists' albums
        df = df.query(
            f"(release_date >= '{start_date.isoformat()}') & (release_date <= '{end_date.isoformat()}') & (album_type != 'compilation') & (various_artists == False)"
        )
        return df

    def get_album(self, album_id: str, market: str = "FR") -> dict:
        """Get Spotify catalog information for a single album.
        https://developer.spotify.com/documentation/web-api/reference/#/operations/get-an-album"""
        params = {"market": market}
        r = self._get(f"albums/{album_id}", params=params)
        return r.json()

    def get_tracks_from_album(
        self, album_id: str, market: str = "FR", limit: int = 50,  offset: int = 0
    ) -> pd.DataFrame:
        """Get Spotify catalog information about an album's tracks.
        Conform to original https://developer.spotify.com/documentation/web-api/reference/#/operations/get-an-albums-tracks"""
        params = {"limit": limit, "market": market, "offset": offset}
        r = self._get(f"albums/{album_id}/tracks", params=params)
        return pd.DataFrame(r.json()["items"])

    def _get_tracks_uris_from_album(
        self, album_id: str, market: str = "FR", limit: int = 50,  offset: int = 0
    ) -> list[str]:
        """Return tracks uris from an album."""
        tracks = self.get_tracks_from_album(album_id, market=market, limit=limit, offset=offset)
        return tracks["uri"].to_list()
    
    def get_devices(self) -> dict:
        """Get information about a user’s available devices.
        Conform to original https://developer.spotify.com/documentation/web-api/reference/get-a-users-available-devices"""
        r = self._get("me/player/devices")
        return r.json()

    def add_to_queue(self, tracks_uris: list[str], device_id: str = None):
        """Add items to the end of the user's current playback queue.
        Adapted from https://developer.spotify.com/documentation/web-api/reference/#/operations/add-to-queue"""
        for track_uri in tracks_uris:  # loop through tracks
            data = {"uri": track_uri, "device_id": device_id}
            self._post("me/player/queue", json=remove_nones(data))

    def create_playlist(
        self,
        name: str,
        public: bool = False,
        collaborative: bool = False,
        description: str = None,
    ):
        """Create a playlist for a Spotify user. (The playlist will be empty until you add tracks.)
        Conform to original https://developer.spotify.com/documentation/web-api/reference/#/operations/create-playlist
        """
        data = {
            "name": name,
            "public": public,
            "collaborative": collaborative,
            "description": description,
        }
        r = self._post(f"users/{self.user_id}/playlists", json=remove_nones(data))
        return r.json()["id"]

    def change_playlist_details(
        self,
        playlist_id: str,
        name: str = None,
        public: bool = None,
        collaborative: bool = None,
        description: str = None,
    ) -> None:
        """Change a playlist's name and public/private state. (The user must, of course, own the playlist.)
        Conform to original https://developer.spotify.com/documentation/web-api/reference/change-playlist-details
        """
        data = {
            "name": name,
            "public": public,
            "collaborative": collaborative,
            "description": description,
        }
        r = self._put(f"playlists/{playlist_id}", json=remove_nones(data))
        if not r.ok:
            raise Exception(r.status_code, r.reason, r.text)

    def get_songs_from_playlist(
        self,
        paylist_id: str,
        market: str = "FR",
        fields: list[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> pd.DataFrame:
        """Get full details of the items of a playlist owned by a Spotify user.
        Conform to original https://developer.spotify.com/documentation/web-api/reference/#/operations/get-playlists-tracks
        """
        params = {"market": market, "fields": fields, "limit": limit, "offset": offset}
        r = self._get(f"playlists/{paylist_id}/tracks", params=remove_nones(params))
        return pd.json_normalize([x["track"] for x in r.json()["items"]])

    def update_playlist_items(self, playlist_id: str, tracks_uris: list[str]) -> None:
        """Either reorder or replace items in a playlist depending on the request's parameters.
        Conform to original https://developer.spotify.com/documentation/web-api/reference/#/operations/reorder-or-replace-playlists-tracks
        """
        data = {"uris": tracks_uris}
        self._put(f"playlists/{playlist_id}/tracks", json=data)

    def get_user_playlists(
        self, contains: str = None, limit: int = 50, offset: int = 0
    ) -> pd.DataFrame:
        """Get a list of the playlists owned or followed by the current Spotify user.
        Optionally provide 'contains', a regex pattern to filter results.
        Adapted from https://developer.spotify.com/documentation/web-api/reference/get-a-list-of-current-users-playlists
        """
        params = {"limit": limit, "offset": offset}
        ls = []
        while True:
            r = self._get("me/playlists", params=params)
            if not r.json()["items"]:
                break

            ls.extend(r.json()["items"])
            params["offset"] += params["limit"]

        df = pd.DataFrame(ls)
        if contains is not None:
            df = df.query(f"name.str.contains('{contains}')")

        return df

    def save_albums(self, ids: list[str]) -> None:
        """Save one or more albums to the current user's 'Your Music' library.
        Conform to original https://developer.spotify.com/documentation/web-api/reference/#/operations/save-albums-user
        """
        self._put("me/albums", json=ids)

    def get_artist_id(self, name: str) -> str:
        """Try to find an artist's id based on their name."""
        params = {"q": name.lower(), "type": "artist"}
        r = self._get("search", params=params)
        df = pd.json_normalize(r.json()["artists"]["items"])
        df.sort_values("popularity", ascending=False, inplace=True)
        df["name"] = df["name"].str.lower()
        artist_id = df.loc[df["name"] == name.lower(), "id"]
        if len(artist_id) > 0:
            return artist_id.iloc[0]
        else:
            raise Exception(
                f"Can't match an artist with this {name=:}, try a different name!"
            )

    def _get_tracks_popularity(self, tracks_ids: list) -> list[str]:
        """Return popularity of a list of tracks.
        Limit is 50 tracks in one batch.
        Adapted from https://developer.spotify.com/documentation/web-api/reference/get-several-tracks
        """
        params = {"ids": ",".join(tracks_ids)}
        r = self._get("tracks", params=params)
        return [track["popularity"] for track in r.json()["tracks"]]

    @backoff.on_predicate(backoff.constant, jitter=None, interval=30)
    def _get_artists_id_from_tracks(
        self, tracks_ids: list, market: str = "FR"
    ) -> list[str]:
        """Return artists' ids featured on a given list of tracks."""
        params = {"ids": ",".join(tracks_ids), "market": market}
        r = self._get("tracks", params=params)

        artists_ids = []
        for track in r.json()["tracks"]:
            track_artists = []
            for artist in track["artists"]:
                track_artists.append(artist["id"])
            artists_ids.append(track_artists)
        return artists_ids

    @backoff.on_predicate(backoff.constant, jitter=None, interval=30)
    def _get_tracks_names(self, tracks_ids: list[str]) -> list[str]:
        """Get tracks uris from an album"""
        params = {"ids": ",".join(tracks_ids), "market": "FR"}
        r = self._get("tracks", params=params)

        tracks_names = []
        for track in r.json()["tracks"]:
            tracks_names.append(track["name"])
        return tracks_names

    def _get_artist_top_songs_helper(
        self,
        artist_id: str,
        include: str = "single",
        exclude: list[str] = None,
        country: str = "FR",
        limit: int = 50,
    ) -> pd.DataFrame:
        """Helper function of get_artist_top_songs"""
        # get albums first
        params = {"country": country, "limit": limit, "include_groups": include}
        r = self._get(f"artists/{artist_id}/albums", params=params)

        df = pd.json_normalize(r.json()["items"])
        if df.empty:
            return pd.DataFrame()

        df.drop_duplicates(
            subset=["name", "total_tracks"],
            keep="first",
            ignore_index=True,
            inplace=True,
        )
        df["release_date"] = df["release_date"].astype("datetime64[ns]")
        if exclude is not None:
            if not isinstance(exclude, list):
                exclude = [exclude]
            df = df[~df["id"].isin(exclude)]

        # remove compilation if any
        df = df[df["album_type"] != "compilation"]

        if df.empty:
            return pd.DataFrame()

        # get songs from albums now
        df["track"] = df["id"].apply(self._get_tracks_uris_from_album)
        df = df.explode("track")
        df["track_id"] = [track.split(":")[-1] for track in df["track"]]

        # get track's name
        track_id_chunks = n_chunks(df["track_id"].to_list(), chunk_size=50)
        tracks_names = []
        for chunk in track_id_chunks:
            tracks_names.extend(self._get_tracks_names(chunk))
        df["track_name"] = tracks_names

        if "appears_on" in include:
            artists_ids = []
            for chunk in track_id_chunks:
                artists_ids.extend(self._get_artists_id_from_tracks(chunk))
            df["artists_ids"] = [",".join(map(str, ls)) for ls in artists_ids]

            df = df[df["artists_ids"].str.contains(artist_id)]
        return df

    def get_artist_top_songs(
        self,
        artist_id: str,
        n: int = 50,
        include: str = "single,album,appears_on",
        method: str = "popularity",
        country: str = "FR",
        exclude: list[str] = None,
    ) -> list[str]:
        """Get n albums of a specified artist; list of uris are returned.
        method: 'recent' / 'random' / 'popularity'
        include: 'appears_on', 'album', 'single' or a combination of any ex. 'appears_on,album,single'
        exclude: albums ids to exclude
        """
        include_list = include.split(",")
        df = pd.concat(
            [
                self._get_artist_top_songs_helper(
                    artist_id, include=group, country=country, exclude=exclude
                )
                for group in include_list
            ]
        )
        df.drop_duplicates(subset="track_name", inplace=True)

        if method == "recent":
            return df.nlargest(n, columns="release_date")["track"].to_list()
        elif method == "popularity":
            tracks_chunks = n_chunks(df["track_id"].to_list(), 50)
            popularity = []
            for chunk in tracks_chunks:
                popularity.extend(self._get_tracks_popularity(chunk))
            df["popularity"] = popularity
            return df.nlargest(n, columns="popularity")["track"].to_list()
        elif method == "random":
            return df["track"].sample(n)
        else:
            raise ValueError(f"'{method}' is not a valid method, try another one.")

    def add_to_playlist(
        self, playlist_id: str, tracks_uris: str, position: int = 0
    ) -> None:
        """Add one or more items to a user's playlist.
        Conform to original https://developer.spotify.com/documentation/web-api/reference/add-tracks-to-playlist
        """
        params = {"uris": ",".join(tracks_uris), "position": position}
        self._post(f"playlists/{playlist_id}/tracks", params=params)

    def update_playlist(
        self,
        playlist_id: str,
        uris: str,
    ) -> None:
        """Either reorder or replace items in a playlist.
        Adapted from https://developer.spotify.com/documentation/web-api/reference/reorder-or-replace-playlists-tracks
        """
        params = {"uris": ','.join(uris)}
        r = self._put(f"playlists/{playlist_id}/tracks", params=params)
        if not r.ok:
            raise Exception(r.status_code, r.reason, r.text)
