import threading
import requests
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from pydantic import BaseModel
from google import genai
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
gemini_api_key = os.getenv("GEMINI_API_KEY")

lock = threading.Lock()
stop_thread = False
esp32_ip = "192.168.20.106" # IP address of the esp32 
playlist = None
speed_kmh = None
sl = .75 # stride length

# Spotipi setup
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id= os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret= os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri="http://127.0.0.1:8888/callback",
        scope="user-modify-playback-state,user-read-playback-state",
        open_browser=False
))

# Gemini api key
Gemini_api_key= os.getenv("GEMINI_API_KEY")

# ----------- Spotify + Gemini Setup -----------

# Gemini output structure
class Output(BaseModel):
    Warm_up: list[str]
    Running: list[str]
    Sprinting: list[str]
    Cooldown: list[str]

def generate_and_queue_workout_playlist():
    # Spotify Auth
    global data,playlist

    # Gemini API Setup
    client = genai.Client(api_key=Gemini_api_key)

    # Load song data
    with open("songs.json") as f:
        data = json.load(f)

    formatted = ""
    for track in data["tracks"]:
        formatted += f"id {track['id']}, name {track['name']}, artists {track['artists']}, duration {track['duration_sec']}, bpm {track['bpm']}, energy {track['energy']}, danceability {track['danceability']}\n"

    # Get response from Gemini
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        # Prompt for gemini
        contents=["You are my workout assistant.\n\n"+
                  f"{formatted}\n"+
                  " above is my liked songs along with metadata such as spotify id, name, artists, duration in seconds, bpm, energy, and danceability."
                  " Your task is to analyze the tracks and return a subset of songs that are ideal for a treadmill workout."
                  " Use the following criteria:"
                    "Warm-up songs (BPM 90–110, moderate energy, high danceability),"
                    "Running songs (BPM 120–150, high energy and danceability),"
                    "Sprinting songs (BPM 150–180+, very high energy preferred),"
                    "Cooldown songs (BPM < 90, low energy and smooth transitions)."
                  " Total time should be less than 1200 seconds."
                  " Return id of each selected songs in each catagory following the response schema."
                  " Don't include songs that are too low in danceability unless they are clearly for cooldown."
                  " Prioritize diversity in BPM and avoid repeating the same artist too many times in each category."],
        config={
            "response_mime_type": "application/json",
            "response_schema": Output,
        }
    )

    # Decode the response
    try:
        playlist = json.loads(response.text)
    except json.JSONDecodeError as e:
        print("Failed to decode Gemini JSON:", e)
        return
    
    # Print no. of songs and its ids
    print("🎵 Gemini-generated playlist (by section):")
    for section, tracks in playlist.items():
        print(f"{section}: {len(tracks)} tracks")


    # Queue all tracks
    all_track_ids = []
    for section in playlist:
        all_track_ids.extend(playlist[section])

    for track_id in all_track_ids:
        try:
            sp.add_to_queue(f"spotify:track:{track_id}")
            print(f"Queued: {track_id}")
            time.sleep(0.3)
        except spotipy.exceptions.SpotifyException as e:
            print(f"Failed to queue {track_id}: {e}")

# ----------- ESP32 Command Section -----------

# Thread that fetch the values from esp32
def get_status(session):
    global  stop_thread, speed_kmh
    while not stop_thread:
        try:
            response = session.get(f"http://{esp32_ip}/status", timeout=5)
            if response.status_code == 200:
                try:
                    status_data = response.json()
                    with lock:
                        speed_kmh = status_data.get("speed_kmh", 0)
                except json.JSONDecodeError:
                    print("[ESP32 Status] Failed to parse JSON.")
            else:
                print(f"[ESP32 Status] Error {response.status_code}")
        except requests.RequestException as e:
            print(f"[ESP32 Status] Connection error: {e}")
        time.sleep(1)

def start_esp32_interface():
    global stop_thread, esp32_ip

    session = requests.Session()

    # Start the background thread
    status_thread = threading.Thread(target=get_status, args=(session,))
    status_thread.daemon = True
    status_thread.start()

    print(f"\n🔌 Connected to ESP32 at http://{esp32_ip}/")

    try:
        while True:
            cmd = input("\nPC >>> ").strip().lower() # To get command from terminal
            if cmd == "exit":
                break
            elif cmd == "start" :

                try:
                    sp.start_playback()
                except Exception as e:
                    print(f"Failed to start song: {e}")
                
                params = {'action': cmd}
                print(params)

                # Send start command
                try:
                    resp = session.get(f"http://{esp32_ip}/command", params=params, timeout=5)
                    if resp.ok:
                        print(f"ESP32 <<< {resp.text}")
                    else:
                        print(f"ESP32 <<< Error: {resp.status_code} - {resp.text}")
                except requests.RequestException as e:
                    print(f"Failed to send command: {e}")

                while True:
                    current=sp.current_user_playing_track()
                    if current and current.get('item'):
                        song_id = current['item']['id']
                    else:
                        print("No track currently playing.")

                    bpm = find_bpm_by_id(song_id,data)
                    speed = round(bpm * sl * 0.06,1)
                    if (speed_kmh != speed) & (speed < 14) & (speed >= 1) :
                        command_input = f'speed {speed}'
                        parts = command_input.lower().strip().split()
                        action = parts[0]
                        params = {'action': action}

                        if len(parts) > 1:
                            params['value'] = parts[1]
                            
                        print(params)
                        try:
                            resp = session.get(f"http://{esp32_ip}/command", params=params, timeout=5)
                            if resp.ok:
                                print(f"ESP32 <<< {resp.text}")
                            else:
                                print(f"ESP32 <<< Error: {resp.status_code} - {resp.text}")
                        except requests.RequestException as e:
                            print(f"Failed to send command: {e}")
                    time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        stop_thread = True
        print("Stopping thread and exiting...")

# As the name says used to get bpm of a song
def find_bpm_by_id(track_id, data):
    for track in data["tracks"]:
        if track["id"] == track_id:
            return track["bpm"]
    return 0.0

# ----------- Main Function -----------
def main():
    print("🎧 Generating treadmill workout playlist using Gemini + Spotify...")
    generate_and_queue_workout_playlist()

    print("\n🔧 Starting ESP32 command interface...")
    start_esp32_interface()

if __name__ == "__main__":
    main()