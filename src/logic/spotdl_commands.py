import os
import re
from PySide6.QtCore import SignalInstance
import requests
from spotdl import Spotdl
import spotdl.utils.config as spotDlConfig
import spotipy
from spotipy.client import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from src.utils.config_manager import PlaylistData

spotdl = None
spotipy_client = None

client_id = None
client_secret = None


def get_user_playlists(user_id: str, found_playlist_signal: SignalInstance):
    global spotipy_client

    if not spotipy_client:
        global client_id
        global client_secret

        if not client_id or not client_secret:
            get_spotdl_config()

        if not client_id or not client_secret:
            print(
                f"Unable to obtain client id and secret: client_id - {client_id} | client_secret - {client_secret}"
            )
            return

        auth_manager = SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )

        spotipy_client = spotipy.Spotify(auth_manager=auth_manager)

    try:
        results = spotipy_client.user_playlists(user_id)
    except SpotifyException as e:
        if "http status: 404" in str(e):
            print(f"Could not find playlists for user ID '{user_id}'.")
            return
        else:
            print(f"An unexpected Spotify API error occurred: {e}")
            return
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Could not find playlists for user ID '{user_id}'.")
            return
        else:
            raise

    while results:
        for playlist in results["items"]:
            if playlist.get("public", True):
                # TODO: ENSURE THAT PRIORITY VALUE IS SET AFTER ADDING TO LIST CARD
                playlist_data: PlaylistData = {
                    "priority": -1,
                    "owner": playlist["owner"]["display_name"],
                    "title": playlist["name"],
                    "total_tracks": playlist["tracks"]["total"],
                    "url": playlist["external_urls"]["spotify"],
                    "id": playlist["id"],
                    "cover_url": playlist["images"][0]["url"],
                    "enabled": True,
                }

                response = requests.get(playlist_data.get("cover_url"))
                cover_bytes = bytes()
                if response.status_code == 200:
                    cover_bytes = response.content

                found_playlist_signal.emit(playlist_data, cover_bytes)

        if results["next"]:
            results = spotipy_client.next(results)
        else:
            results = None


def download_cover_image(output_directory, cover_url: str) -> None:
    try:
        cover_image_path = os.path.join(output_directory, "cover.jpg")

        if os.path.exists(cover_image_path):
            print(f"Cover image already exists at: {cover_image_path}")
            return

        response = requests.get(cover_url)
        if response.status_code == 200:
            with open(cover_image_path, "wb") as file:
                file.write(response.content)
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
            get_spotdl_config()

        if not client_id or not client_secret:
            print(
                f"Unable to obtain client id and secret: client_id - {client_id} | client_secret - {client_secret}"
            )
            return

        spotdl = Spotdl(
            client_id=client_id,
            client_secret=client_secret,
            downloader_settings={
                "output": output_directory,
            },
        )

    elif isinstance(spotdl, Spotdl):
        # Update output directory of current instance
        spotdl.downloader.settings["output"] = output_directory
    else:
        raise Exception(f"Error initialising Spotdl instance: {spotdl}")


def syncPlaylist(
    playlist: PlaylistData, progress_signal: SignalInstance, playlist_index: int = -1
):
    print(f"\n== Starting sync for '{playlist['title']}' ==")

    # Get the spotdl configuration
    p_title = playlist["title"]
    p_url = playlist["url"]

    # Configured output directory for downloads
    output_directory = f"playlists/{_sanitize_filename(p_title)}"

    # Get the spotdl instance
    init_spotdl(output_directory)

    # Create folder for the playlist
    os.makedirs(output_directory, exist_ok=True)

    # Download the playlist cover
    download_cover_image(output_directory, playlist.get("cover_url"))

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
        # TODO: ADD PLAYIST NAME ALSO
        total_tracks = len(songs)
        for i, song in enumerate(songs):
            if progress_signal:
                message = (
                    f"{p_title} : synchronizing {song.name}... {i + 1}/{total_tracks}"
                )
                progress_signal.emit(message, playlist_index)
            download = spotdl.download(song)
            print(f"Successfully downloaded: {song.name} at {download[1]}.")
    except Exception as e:
        print(f"Error while synchronizing playlist '{p_title}': {e}")


def get_spotdl_config():
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


def _sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitiza una cadena para usarla como nombre de archivo/directorio.

    1. Elimina caracteres no válidos para sistemas de archivos comunes.
    2. Reemplaza espacios con guiones bajos (opcional, pero ayuda).
    3. Recorta la cadena a una longitud máxima.
    """

    # 1. Reemplazar caracteres ilegales con un guion bajo '_'
    # Caracteres ilegales comunes: / \ : * ? " < > |
    # También incluimos caracteres de control (0x00-0x1F)
    safe_filename = re.sub(r'[\\/:*?"<>|]+', "_", filename)

    # Opcional: Eliminar espacios iniciales/finales y múltiples guiones
    safe_filename = safe_filename.strip()
    safe_filename = re.sub(r"_{2,}", "_", safe_filename)

    # 2. Recortar la longitud
    if len(safe_filename) > max_length:
        safe_filename = safe_filename[:max_length]
        # Asegurarse de que el recorte no termine en un guion
        if safe_filename.endswith("_"):
            safe_filename = safe_filename[:-1]

    # También eliminar nombres reservados de Windows (CON, PRN, AUX, etc.)
    reserved_names = {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}
    if safe_filename.upper() in reserved_names:
        safe_filename = "_" + safe_filename

    return safe_filename
