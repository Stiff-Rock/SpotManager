import os
import requests
from spotdl import Spotdl
import spotdl.utils.config as spotDlConfig
import spotipy
from spotipy import SpotifyClientCredentials

client_id = None
client_secret = None


def download_cover_image(output_directory, p_url):
    print("Downloading playlist cover...")
    # Get the cover from the spotify api
    auth_manager = SpotifyClientCredentials(
        client_id=client_id, client_secret=client_secret
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    playlist_id = p_url.split("/")[-1].split("?")[0]
    playlist = sp.playlist(playlist_id)

    if not playlist:
        print(f"Playlist not foudn with url {p_url}")
        return

    if playlist["images"]:
        largest_image = max(playlist["images"], key=lambda x: x.get("width", 0))

        cover_image_path = os.path.join(output_directory, "cover.jpg")
        cover_url = largest_image["url"]

        response = requests.get(cover_url)
        if response.status_code == 200:
            with open(cover_image_path, "wb") as file:
                file.write(response.content)
            print("- Downloaded playlist cover")
        else:
            print(f"Failed to download cover image: {cover_url}")


def init_spotdl(output_directory):
    # Get the configuration and initialise spotdl
    config = None

    try:
        config = spotDlConfig.get_config()
    except spotDlConfig.ConfigError:
        config = spotDlConfig.DEFAULT_CONFIG
        pass

    if not config:
        raise Exception("Could not find spotdl config file")

    client_id = config["client_id"]
    client_secret = config["client_secret"]

    return Spotdl(
        client_id=client_id,
        client_secret=client_secret,
        downloader_settings={"output": output_directory},
    )


def syncPlaylist(playlist):
    print(f"Starting sync for '{playlist['title']}'")

    # Get the spotdl configuration
    p_title = playlist["title"]
    p_url = playlist["url"]

    # Configured output directory for downloads
    output_directory = f"{p_title}"

    # Get the spotdl instance
    spotdl = init_spotdl(output_directory)

    # Create folder for the playlist
    os.makedirs(output_directory, exist_ok=True)

    # Download the playlist cover
    download_cover_image(output_directory, p_url)

    # Download each song from the playlist
    try:
        songs = spotdl.search([p_url])

        if not songs:
            print(f"Could not find playlist '{p_title}' with given Url")
            return

        # Download each song
        for song in songs:
            download = spotdl.download(song)
            print(f"Successfully downloaded: {song.name} at {download[1]}.")
    except Exception as e:
        print(f"Error while synchronizing playlist '{p_title}': {e}")
