import os
import requests


class Refresh:
    def __init__(self):
        self.refresh_token = os.environ.get("SPOTIFY_REFRESH_TOKEN")
        self.base_64 = os.environ.get("SPOTIFY_BASE64")

    def refresh(self):
        url = "https://accounts.spotify.com/api/token"
        response = requests.post(url,
                                 data={"grant_type": "refresh_token",
                                       "refresh_token": self.refresh_token},
                                 headers={"Authorization": "Basic " + self.base_64})
        response_json = response.json()
        return response_json["access_token"]
