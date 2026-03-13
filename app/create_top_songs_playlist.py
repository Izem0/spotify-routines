"""Create a Spotify playlist with the top songs of a specific artist."""

import jmespath
from config import settings
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from utils import setup_logger, timer

ARTIST_NAME = "Asfar Shamsi"
log = setup_logger("spotify-top-songs")


def get_artist_albums_all(spotipy: Spotify, artist_id: str) -> list:
    """Get all albums of an artist, handling pagination."""
    albums = []
    limit = 50
    offset = 0

    while True:
        response = spotipy.artist_albums(artist_id, limit=limit, offset=offset)
        albums.extend(response["items"])
        if response["next"] is None:
            break
        offset += limit

    return albums


def get_tracks(spotipy: Spotify, track_ids: list) -> list:
    """Get track details for a list of track IDs, handling batching."""
    tracks = []
    batch_size = 50

    for i in range(0, len(track_ids), batch_size):
        batch_ids = track_ids[i : i + batch_size]
        response = spotipy.tracks(batch_ids)
        tracks.extend(response["tracks"])

    return tracks


def get_user_playlists(spotipy: Spotify) -> list:
    """Get all playlists of the current user, handling pagination."""
    playlists = []
    limit = 50
    offset = 0

    while True:
        response = spotipy.current_user_playlists(limit=limit, offset=offset)
        playlists.extend(response["items"])
        if response["next"] is None:
            break
        offset += limit

    return playlists


@timer(logger=log)
def main():
    # instantiate the class
    spotipy = Spotify(
        auth_manager=SpotifyOAuth(
            client_id=settings.SPOTIPY_CLIENT_ID,
            client_secret=settings.SPOTIPY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIPY_REDIRECT_URI,
            scope=settings.SPOTIPY_SCOPE,
        )
    )

    # get artist id
    results = spotipy.search(ARTIST_NAME, type="artist")
    if not results["artists"]["items"]:
        log.error("No result found")
        return

    artist = results["artists"]["items"][0]
    if artist["name"].lower() != ARTIST_NAME.lower():
        log.error(f"Artist not found, results: {results}")
        return

    playlist_name = f"{artist['name']}: Top Songs"
    playlists = get_user_playlists(spotipy)
    existing_playlist = next(
        (pl for pl in playlists if pl["name"] == playlist_name), None
    )
    if existing_playlist:
        log.warning(f"Playlist '{playlist_name}' already exists. Exiting.")
        return

    # get all albums of the artist
    albums = get_artist_albums_all(spotipy, artist["id"])

    # get all unique tracks from the albums
    album_tracks = []
    for album in albums:
        tracks = spotipy.album_tracks(album["id"])
        for track in tracks["items"]:
            album_tracks.append(track)

    # filter tracks to only include those where the given artist is one of the main artists
    filtered_tracks = jmespath.search(
        f"[?contains(artists[].id, '{artist['id']}')]", album_tracks
    )
    log.info(f"Found {len(filtered_tracks)} tracks for artist '{ARTIST_NAME}'")

    # get track details to access popularity
    tracks = get_tracks(spotipy, track_ids=[track["id"] for track in filtered_tracks])

    # sort tracks by popularity
    sorted_tracks = sorted(tracks, key=lambda x: x["popularity"], reverse=True)

    # create playlist if it doesn't exist
    playlist = spotipy.user_playlist_create(
        user=spotipy.current_user()["id"],
        name=playlist_name,
        description=f"Top songs of {artist['name']}, "
        f"ordered by popularity from highest to lowest. "
        f"This playlist is updated every friday at 00:00:00 UTC.",
    )

    # add songs to the playlist
    spotipy.playlist_add_items(playlist["id"], [track["id"] for track in sorted_tracks])


if __name__ == "__main__":
    main()
