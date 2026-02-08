import json
import os
import requests
from gtts import gTTS
import time
import io
import base64

# --- SETTINGS ---
# Change these variables according to your needs
INPUT_FILE = "frases.txt"
DECK_NAME = "Spanish"  # The exact name of the deck in Anki
MODEL_NAME = "Basic"   # The name of the note type (usually "Basic")
CARD_LIMIT = 10        # How many cards to add per run
AUDIO_LANG = 'es'      # Language of the audio to be generated (e.g., 'es' for Spanish)

# AnkiConnect URL (usually doesn't need to be changed)
ANKI_CONNECT_URL = "http://localhost:8765"

def invoke_anki_connect(action, **params):
    """Helper function to make a request to the AnkiConnect API."""
    payload = {"action": action, "version": 6, "params": params}
    try:
        response = requests.post(ANKI_CONNECT_URL, json=payload)
        response.raise_for_status()  # Raise an error for bad HTTP responses (4xx or 5xx)
        response_json = response.json()
        if 'error' in response_json and response_json['error'] is not None:
            print(f"Error received from AnkiConnect: {response_json['error']}")
            return None
        return response_json['result']
    except requests.exceptions.RequestException as e:
        print(f"Could not connect to AnkiConnect. Please ensure Anki is running and the AnkiConnect add-on is installed. Error: {e}")
        return None

def run_card_creation_logic(log_callback=print):
    """
    The core logic for creating Anki cards.
    Accepts a callback function to handle logging.
    """
    log_callback("Starting script to add cards to Anki...")

    # 1. Check if Anki is accessible
    if invoke_anki_connect('deckNames') is None:
        return  # The error message is already printed by the invoke function

    # 2. Read the phrases file
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and '|' in line]
    except FileNotFoundError:
        log_callback(f"Error: File '{INPUT_FILE}' not found. Please create this file in the same directory as the script.")
        return

    cards_added = 0
    for i, line in enumerate(lines):
        if cards_added >= CARD_LIMIT:
            log_callback(f"\nCard limit of {CARD_LIMIT} reached. Exiting.")
            break

        front, back = [part.strip() for part in line.split('|', 1)]
        
        log_callback(f"\nProcessing card {cards_added + 1}/{CARD_LIMIT}: '{front}'")

        # 4. Check if the card already exists to avoid duplicates
        query = f'"deck:{DECK_NAME}" "Front:{front}"'
        if invoke_anki_connect('findNotes', query=query):
            log_callback(f"Card for '{front}' already exists. Skipping.")
            continue

        # 5. Generate and store audio
        audio_filename = f"auto_anki_{int(time.time() * 1000)}.mp3"
        try:
            tts = gTTS(text=front, lang=AUDIO_LANG)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio_bytes = mp3_fp.read()
            audio_data_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            if invoke_anki_connect('storeMediaFile', filename=audio_filename, data=audio_data_b64) is None:
                log_callback("Failed to store the audio file. Skipping this card.")
                continue
            log_callback(f"  Audio '{audio_filename}' generated and stored.")
        except Exception as e:
            log_callback(f"  Error generating audio for '{front}': {e}")
            continue

        # 6. Assemble and add the note
        front_field_with_audio = f"{front} [sound:{audio_filename}]"
        note = {
            "deckName": DECK_NAME,
            "modelName": MODEL_NAME,
            "fields": {"Front": front_field_with_audio, "Back": back},
            "tags": ["auto-gerado"]
        }

        if invoke_anki_connect('addNote', note=note):
            log_callback(f"  Card for '{front}' added successfully!")
            cards_added += 1
        else:
            log_callback(f"  Failed to add card for '{front}'.")

    log_callback(f"\nProcess complete. Total cards added: {cards_added}.")

def main():
    """Main function for command-line execution."""
    run_card_creation_logic(log_callback=print)

if __name__ == "__main__":
    main()