import os
import requests
from spotdl import Spotdl
import spotdl.utils.config as spotDlConfig
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

spotdl = None
spotipy_client = None

client_id = None
client_secret = None

# TODO: GET THE PLAYLISTS FROM THE PROFILE AND NOT FROM THE JSON FILE


def get_user_playlists(user_id: str):
    global spotipy_client

    if not spotipy_client:
        global client_id
        global client_secret

        if not client_id or not client_secret:
            get_config()

        if not client_id or not client_secret:
            print(
                f"Unable to obtain client id and secret: client_id - {client_id} | client_secret - {client_secret}"
            )
            return

        auth_manager = SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )

        spotipy_client = spotipy.Spotify(auth_manager=auth_manager)

    results = spotipy_client.user_playlists(user_id)
    all_playlists = []

    while results:
        for playlist in results["items"]:
            if playlist.get("public", True):
                playlist_data = {
                    "title": playlist["name"],
                    "url": playlist["external_urls"]["spotify"],
                    "total_tracks": playlist["tracks"]["total"],
                    "owner": playlist["owner"]["display_name"],
                }
                all_playlists.append(playlist_data)

        if results["next"]:
            results = spotipy_client.next(results)
        else:
            results = None

    return all_playlists


def download_cover_image(output_directory, p_url):
    try:
        global spotipy_client

        if not spotipy_client:
            global client_id
            global client_secret

            if not client_id or not client_secret:
                get_config()

            if not client_id or not client_secret:
                print(
                    f"Unable to obtain client id and secret: client_id - {client_id} | client_secret - {client_secret}"
                )
                return

            print("Downloading playlist cover... ", end="")

            # Get the cover from the spotify api
            auth_manager = spotipy.SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
            spotipy_client = spotipy.Spotify(auth_manager=auth_manager)

        playlist_id = p_url.split("/")[-1].split("?")[0]
        playlist = spotipy_client.playlist(playlist_id)

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
                print("Done!")
            else:
                print(f"Failed to download cover image: {cover_url}")
    except Exception as e:
        print(f"Faield to obtain playlist cover: {e}")


def init_spotdl(output_directory: str):
    global spotdl

    if not spotdl:
        # Initialise spotdl
        global client_id
        global client_secret

        if not client_id or not client_secret:
            get_config()

        if not client_id or not client_secret:
            print(
                f"Unable to obtain client id and secret: client_id - {client_id} | client_secret - {client_secret}"
            )
            return

        spotdl = Spotdl(
            client_id=client_id,
            client_secret=client_secret,
            downloader_settings={"output": output_directory},
        )
    elif isinstance(spotdl, Spotdl):
        # Update output directory of current instance
        spotdl.downloader.settings["output"] = output_directory
    else:
        raise Exception(f"Error initialising Spotdl instance: {spotdl}")


def syncPlaylist(playlist):
    print(f"\n== Starting sync for '{playlist['title']}' ==")

    # Get the spotdl configuration
    p_title = playlist["title"]
    p_url = playlist["url"]

    # Configured output directory for downloads
    output_directory = f"playlists/{p_title}"

    # Get the spotdl instance
    init_spotdl(output_directory)

    # Create folder for the playlist
    os.makedirs(output_directory, exist_ok=True)

    # Download the playlist cover
    download_cover_image(output_directory, p_url)

    # Download each song from the playlist
    global spotdl

    if not spotdl:
        print(f"Error synchronizing playlists: Spotdl wasn't initialised ({spotdl})")
        return

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


def get_config():
    # Get the configuration
    config = None

    try:
        config = spotDlConfig.get_config()
    except spotDlConfig.ConfigError:
        config = spotDlConfig.DEFAULT_CONFIG
        pass

    if config is None:
        raise Exception("Could not find spotdl config file")

    global client_id
    global client_secret

    client_id = config["client_id"]
    client_secret = config["client_secret"]
