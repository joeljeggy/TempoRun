# TempoRun: Treadmill Control and Music Sync

TempoRun is a web application that synchronizes music to a treadmill workout, dynamically adjusting the target speed based on the currently playing song's beats per minute (BPM). It uses the Google Gemini API to generate a workout-optimized Spotify playlist and a Flask server to communicate with both Spotify and a dedicated ESP32 treadmill interface.

## 🌟 Features

* **Treadmill Control:** Send `start`, `pause`, and `stop` commands to the ESP32 hardware interface.
* **Real-time Metrics:** Display current treadmill status, speed, distance, time, target speed, and calories in a web interface.
* **AI Playlist Generation:** Uses the **Gemini 2.5 Pro API** to analyze a list of liked songs (from `songs.json`) and generate a structured workout playlist: **Warm-up, Running, Sprinting, and Cooldown**.
* **Music-to-Speed Sync:** Calculates the target treadmill speed in km/h based on the current track's BPM and defined stride lengths (`sl` and `run_sl`).
* **Speed Cutout:** An optional safety feature that, when enabled, halves the calculated BPM (and thus the target speed) if the calculated target speed exceeds a user-defined threshold (default 10 km/h).
* **Spotify Player Controls:** Basic music player functionality including Play/Pause, Next Track, and Previous Track.

## ⚙️ Setup and Prerequisites

### Environment Variables

You must create a `.env` file in the root directory to store your credentials.

| Variable | Description |
| :--- | :--- |
| `SPOTIFY_CLIENT_ID` | Your Spotify Developer Client ID. |
| `SPOTIFY_CLIENT_SECRET` | Your Spotify Developer Client Secret. |
| `GEMINI_API_KEY` | Your Google AI Studio API Key for Gemini. |

### Hardware

* **ESP32/Microcontroller:** An ESP32 (or similar) is required to interface with the treadmill.
* **IP Address:** The Flask app expects the ESP32 to be available at a specific IP address (default: `192.168.20.106`). This must be configurable in `app.py`.

### Spotify Scope

The application requires the following Spotify scope: `user-modify-playback-state,user-read-playback-state`.

### Additional Files

* **`songs.json`:** This file must contain a list of tracks with metadata (`id`, `name`, `artists`, `duration_sec`, `bpm`, `energy`, `danceability`) for the Gemini model to analyze and build the playlist.

## 🚀 Running the Application

1.  **Dependencies:** Install the required Python packages (e.g., `flask`, `requests`, `spotipy`, `pydantic`, `google-genai`, `python-dotenv`).

2.  **Run:** Execute the main application file:
    ```bash
    python app.py
    ```
    The application will start two threads: one for the Flask web server (on `http://0.0.0.0:5000`) and one for the ESP32 command interface.

## 💻 Usage

### Main Interface (`/`)

* **Start/Pause/Stop:** Buttons to control the treadmill.
* **Generate Playlist:** Set the desired workout time (between 5 and 60 minutes) and click `🎧 Generate Playlist`. This clears the current Spotify queue and adds the new, AI-generated tracks.

### Admin Panel (`/admin`)

The admin page is for advanced tuning of the system.

* **Stride Lengths:** Adjust and save the following stride lengths, which are used in the speed calculation:
    * `walk_sl` (min 0.3, max 1.5)
    * `sprint_sl` (min 0.3, max 1.5)
    * `run_sl` (min 0.3, max 2.5)
* **Clear Queue:** A button to clear the currently queued tracks on Spotify.
