import requests
from datetime import datetime
from prettytable import PrettyTable
from spotify_module.refresh import Refresh


class Spotify:
    def __init__(self):
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

    def get_new_releases(self, artists, n_days=7, print_table=True):
        print("Getting new releases ...")
        # get artist's new releases
        new_releases = []
        albums_ids = []
        tracks_names = []
        for artist_name, artist_id in artists.items():
            # request
            end_point = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
            params = {'country': 'FR', 'limit': '50', "include_groups": "album,single,appears_on"}
            response = requests.get(end_point, headers=self.headers, params=params)
            response_json = response.json()
            # pprint.pp(response_json)

            for item in response_json["items"]:
                # get track info
                album_group = item["album_group"]
                album_type = item["album_type"]
                artists = item["artists"][0]["name"]
                track_id = item["id"]
                release_date_raw = item["release_date"]
                track_name_raw = item["name"]
                track_name = track_name_raw if len(track_name_raw) <= 50 else track_name_raw[:50]  # cut long names

                # get only new tracks (released less than n_days ago)
                release_date = datetime.strptime(release_date_raw, "%Y-%m-%d") \
                    if len(release_date_raw) > 4 \
                    else datetime.strptime(release_date_raw, "%Y")
                delta = datetime.today() - release_date

                if delta.days <= n_days \
                        and delta.days != -1 \
                        and track_name not in tracks_names \
                        and album_type != "compilation" \
                        and artists != "Various Artists":
                    new_releases.append([artist_name, album_group, album_type, track_name, delta.days])
                    tracks_names.append(track_name)
                    albums_ids.append(track_id)

        if print_table:
            pretty_table = PrettyTable()
            pretty_table.field_names = ["Artist", "Album group", "Album type", "Name", "Days ago"]
            pretty_table.add_rows(new_releases)
            print(pretty_table)

        return albums_ids

    def get_tracks_from_albums(self, albums_ids):
        print("Getting tracks from albums ...")
        tracks_uris = []
        for album_id in albums_ids:
            # request
            end_point = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
            response = requests.get(end_point, headers=self.headers, params={"market": "FR", "limit": "50"})
            response_json = response.json()
            # pprint.pp(response_json)
            for item in response_json["items"]:
                # get artists on the song
                artists = [artist["name"] for artist in item["artists"]]

                # if no favorite artist is in the album, skip
                if len(set(self.favorite_artists.keys()).intersection(set(artists))) == 0:
                    continue
                uri = item["uri"]
                tracks_uris.append(uri)

        return tracks_uris

    def get_devices(self):
        # request
        end_point = "https://api.spotify.com/v1/me/player/devices"
        response = requests.get(end_point, headers=self.headers)
        response_json = response.json()
        devices = response_json["devices"]

        return devices

    def add_to_queue(self, tracks_uris, device_id):
        print("Adding to queue ...")
        # request
        end_point = "https://api.spotify.com/v1/me/player/queue"
        for track_uri in tracks_uris:
            requests.post(end_point, headers=self.headers, params={"uri": f"{track_uri}",
                                                                   "device_id": f"{device_id}"})
