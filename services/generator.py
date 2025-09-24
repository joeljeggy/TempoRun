import json
import time
from typing import List, Dict

from pydantic import BaseModel
from google import genai
import spotipy

# These will be provided by app via injection or import-time linkage
sl = 0.75
run_sl = 1.2
Gemini_api_key = None
sp: spotipy.Spotify | None = None

class Output(BaseModel):
    Warm_up: List[str]
    Running: List[str]
    Sprinting: List[str]
    Cooldown: List[str]


def configure(env: Dict):
    global sl, run_sl, Gemini_api_key, sp
    sl = env.get("sl", sl)
    run_sl = env.get("run_sl", run_sl)
    Gemini_api_key = env.get("Gemini_api_key", Gemini_api_key)
    sp = env.get("sp", sp)


def generate_and_queue_workout_playlist(workout_time_limit_sec: int,
                                         speed_cutout_enabled: int,
                                         speed_cutout_value: int) -> Dict:
    client = genai.Client(api_key=Gemini_api_key)

    with open("songs.json") as f:
        data = json.load(f)

    formatted = ""
    for track in data["tracks"]:
        speed = round(track['bpm'] * sl * 0.06, 1)
        if speed > 6:
            speed = round(track['bpm'] * run_sl * 0.06, 1)
        if speed > 19:
            continue
        if speed_cutout_enabled == 1:
            if speed > speed_cutout_value or speed > 14:
                speed = round((track['bpm'] / 2) * sl * 0.06, 1)
                if speed > 6:
                    speed = round((track['bpm'] / 2) * run_sl * 0.06, 1)

        formatted += f"id {track['id']}, name {track['name']}, artists {track['artists']}, duration {track['duration_sec']}, speed {speed}, energy {track['energy']}, danceability {track['danceability']}\n"

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[
            "You are my workout assistant.\n\n" +
            f"{formatted}\n" +
            " above is my liked songs along with metadata such as spotify id, name, artists, duration in seconds, speed in km/h(1 to 14), energy, and danceability."
            " Your task is to analyze the tracks and return a subset of songs that are ideal for a treadmill workout."
            " Use the following criteria:"
            "Warm-up songs (low speed, moderate energy, high danceability),"
            "Running songs (medium speed, high energy and danceability),"
            "Sprinting songs (high speed, very high energy preferred),"
            "Cooldown songs (low speed, low energy and smooth transitions)."
            f" Total time should be less than {workout_time_limit_sec} seconds."
            " Return id of each selected songs in each catagory following the response schema."
            " Don't include songs that are too low in danceability unless they are clearly for cooldown."
            " Prioritize diversity in BPM and avoid repeating the same artist too many times in each category."
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": Output,
        }
    )

    try:
        playlist = json.loads(response.text)
    except json.JSONDecodeError as e:
        print("Failed to decode Gemini JSON:", e)
        return {}

    print("🎵 Gemini-generated playlist (by section):")
    for section, tracks in playlist.items():
        print(f"{section}: {len(tracks)} tracks")

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

    return playlist
