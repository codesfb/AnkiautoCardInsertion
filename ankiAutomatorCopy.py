import json
import os
import requests
from gtts import gTTS
import time
import io
import base64

# AnkiConnect URL (usually doesn't need to be changed)
ANKI_CONNECT_URL = "http://localhost:8765"

def invoke_anki_connect(action, *, log_callback=print, **params):
    """Helper function to make a request to the AnkiConnect API."""
    payload = {"action": action, "version": 6, "params": params}
    try:
        response = requests.post(ANKI_CONNECT_URL, json=payload)
        response.raise_for_status()  # Raise an error for bad HTTP responses (4xx or 5xx)
        response_json = response.json()
        if 'error' in response_json and response_json['error'] is not None:
            log_callback(f"Error received from AnkiConnect: {response_json['error']}")
            return None
        return response_json['result']
    except requests.exceptions.RequestException as e:
        log_callback(f"Could not connect to AnkiConnect. Please ensure Anki is running and the AnkiConnect add-on is installed. Error: {e}")
        return None

def run_card_creation_logic(log_callback=print):
    """
    The core logic for creating Anki cards.
    Accepts a callback function to handle logging.
    """
    log_callback("Starting script to add cards to Anki...")

    # --- Load Settings from config.json ---
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        log_callback("Configuration loaded from config.json.")
    except FileNotFoundError:
        log_callback("Error: config.json not found. Please create it.")
        return
    except json.JSONDecodeError:
        log_callback("Error: config.json is not a valid JSON file.")
        return

    # --- Validate required config keys ---
    required_keys = ["input_file", "deck_name", "model_name", "card_limit", "audio_lang"]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        log_callback(f"Error: Missing required keys in config.json: {', '.join(missing_keys)}")
        return

    # 1. Check if Anki is accessible
    if invoke_anki_connect('deckNames', log_callback=log_callback) is None:
        return  # The error message is already printed by the invoke function

    # 2. Read the phrases file
    try:
        with open(config['input_file'], 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and '|' in line]
    except FileNotFoundError:
        log_callback(f"Error: Input file '{config['input_file']}' not found.")
        return

    cards_added = 0
    for i, line in enumerate(lines):
        if cards_added >= config['card_limit']:
            log_callback(f"\nCard limit of {config['card_limit']} reached. Exiting.")
            break

        front, back = [part.strip() for part in line.split('|', 1)]
        
        log_callback(f"\nProcessing card {cards_added + 1}/{config['card_limit']}: '{front}'")

        # 4. Check if the card already exists to avoid duplicates
        query = f'"deck:{config["deck_name"]}" "Front:{front}"'
        if invoke_anki_connect('findNotes', query=query, log_callback=log_callback):
            log_callback(f"Card for '{front}' already exists. Skipping.")
            continue

        # 5. Generate and store audio
        audio_filename = f"auto_anki_{int(time.time() * 1000)}.mp3"
        try:
            tts = gTTS(text=front, lang=config['audio_lang'])
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio_bytes = mp3_fp.read()
            audio_data_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            if invoke_anki_connect('storeMediaFile', filename=audio_filename, data=audio_data_b64, log_callback=log_callback) is None:
                log_callback("Failed to store the audio file. Skipping this card.")
                continue
            log_callback(f"  Audio '{audio_filename}' generated and stored.")
        except Exception as e:
            log_callback(f"  Error generating audio for '{front}': {e}")
            continue

        # 6. Assemble and add the note
        front_field_with_audio = f"{front} [sound:{audio_filename}]"
        note = {
            "deckName": config['deck_name'],
            "modelName": config['model_name'],
            "fields": {"Front": front_field_with_audio, "Back": back},
            "tags": ["auto-gerado"]
        }

        if invoke_anki_connect('addNote', note=note, log_callback=log_callback):
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