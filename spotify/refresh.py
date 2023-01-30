import requests


class Refresh:
    """Refresh Spotify Token"""
    def __init__(self, refresh_token, base_64):
        self.refresh_token = refresh_token
        self.base_64 = base_64

    def refresh(self):
        url = "https://accounts.spotify.com/api/token"
        response = requests.post(url,
                                 data={"grant_type": "refresh_token",
                                       "refresh_token": self.refresh_token},
                                 headers={"Authorization": "Basic " + self.base_64})
        response_json = response.json()
        return response_json["access_token"]
