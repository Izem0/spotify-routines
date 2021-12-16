import requests
import json
from datetime import datetime
from prettytable import PrettyTable
from spotify_module.refresh import Refresh


class Spotify:
    def __init__(self):
        self.user_id = "1181713624"
        self.release_radar_id = "37i9dQZEVXbkf1UTJ14JFi"
        self.release_radar_tracks = []
        self.spotify_token = Refresh().refresh()
        self.headers = {"Accept": "application/json",
                        "Content-type": "application/json",
                        "Authorization": f"Bearer {self.spotify_token}"}
        self.favorite_artists = {}

    def get_favorite_artists(self):
        print("Getting favorite artists ...")
        # setting request up
        params = {"type": "artist",
                  "limit": "50"}
        # make first request to get the number of artists I follow
        end_point = "https://api.spotify.com/v1/me/following"

        # loop n times to get all artists id (limit: 50 artists per request)
        next_artist = -1
        count = 0
        while next_artist is not None:
            if count == 0:
                params["after"] = None
            else:
                params["after"] = next_artist

            response = requests.get(end_point, headers=self.headers, params=params)
            response_json = response.json()

            for item in response_json["artists"]["items"]:
                artist_name = item["name"]
                artist_id = item["id"]
                self.favorite_artists[artist_name] = artist_id

            next_artist = response_json["artists"]["cursors"].get("after")
            count += 1

        return self.favorite_artists

    def get_new_releases(self, artists, start_date="", end_date=""):
        print("Getting new releases ...")

        # get artist's new releases
        new_releases, albums_ids, tracks_names = [], [], []
        for artist_name, artist_id in artists.items():
            # request
            end_point = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
            params = {'country': 'FR', 'limit': '50', "include_groups": "album,single,appears_on"}
            response = requests.get(end_point, headers=self.headers, params=params)
            response_json = response.json()

            for item in response_json["items"]:

                release_date = item["release_date"]

                if release_date < start_date or release_date > end_date:
                    continue

                # get track info
                album_group = item["album_group"]
                album_type = item["album_type"]
                artists = item["artists"][0]["name"]
                track_id = item["id"]
                release_date_formatted = datetime.strptime(release_date, '%Y-%m-%d').strftime('%a %d %b.')
                track_name_raw = item["name"]
                track_name = track_name_raw[:50]  # cut long names

                # get tracks under certain conditions
                if track_name not in tracks_names \
                        and album_type != "compilation" \
                        and artists != "Various Artists":
                    new_releases.append([artist_name, album_group, album_type, track_name, release_date_formatted])
                    tracks_names.append(track_name)
                    if album_group != "album":  # get only singles for later adding to playlist
                        albums_ids.append(track_id)

        pretty_table = PrettyTable()
        pretty_table.field_names = ["Artist", "Album group", "Album type", "Name", "Release date"]
        pretty_table.add_rows(new_releases)
        print(pretty_table.get_string(sortby="Album group"))

        # print some info
        print(f"Found {len(new_releases)} new releases "
              f"({datetime.strptime(start_date, '%Y-%m-%d').strftime('%a %d %b.')} - "
              f"{datetime.strptime(end_date, '%Y-%m-%d').strftime('%a %d %b.')}).")

        return albums_ids

    def get_tracks_from_albums(self, albums_ids):
        print("Getting tracks from albums ...")
        tracks_uris = {}
        for album_id in albums_ids:
            # request
            end_point = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
            response = requests.get(end_point, headers=self.headers, params={"market": "FR", "limit": "50"})
            response_json = response.json()

            for item in response_json["items"]:
                # get artists on the song
                artists = [artist["name"] for artist in item["artists"]]

                # if no favorite artist is on the album, skip
                if len(set(self.favorite_artists.keys()).intersection(set(artists))) == 0:
                    continue
                uri = item["uri"]
                name = item["name"]
                tracks_uris[uri] = name

        return tracks_uris

    def get_devices(self):
        # request
        end_point = "https://api.spotify.com/v1/me/player/devices"
        response = requests.get(end_point, headers=self.headers)
        response_json = response.json()
        devices = response_json["devices"]

        return devices

    def add_to_queue(self, tracks_uris, device_id):
        # print("Adding to queue ...")

        # request
        end_point = "https://api.spotify.com/v1/me/player/queue"
        for track_uri in tracks_uris:          # loop through tracks
            params = {"uri": f"{track_uri}", "device_id": f"{device_id}"}
            requests.post(end_point, headers=self.headers, params=params)

    def create_playlist(self, playlist_name):
        print("Creating playlist ...")

        # request
        end_point = f"https://api.spotify.com/v1/users/{self.user_id}/playlists"
        data = {'name': playlist_name,
                "public": "false"}
        response = requests.post(end_point, headers=self.headers, data=json.dumps(data))
        response_json = response.json()

        return response_json["id"]

    def get_songs_from_release_radar(self):
        # print("Getting songs from official release radar ...")

        # request
        end_point = f"https://api.spotify.com/v1/playlists/{self.release_radar_id}/tracks"
        # params = {"fields": "items(track(name)"}
        response = requests.get(end_point, headers=self.headers)
        response_json = response.json()

        # parse track names
        release_radar_tracks_names = [item["track"]["album"].get("name")
                                      for item in response_json["items"]
                                      if item["track"] is not None]
        return release_radar_tracks_names

    def add_to_playlist(self, tracks_uris, playlist_id):
        print("Adding songs to playlist ...")

        # get new release already present in official release radar
        release_radar_tracks_names = self.get_songs_from_release_radar()

        # keep only uris not in release radar
        tracks_uris_new = {uri for uri in tracks_uris.keys() if tracks_uris[uri] not in release_radar_tracks_names}

        # make a long string of tracks uris
        tracks_uris_list = ','.join(tracks_uris_new)

        # request
        end_point = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        params = {"uris": tracks_uris_list}
        requests.post(end_point, headers=self.headers, params=params)
