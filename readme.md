This program helps me with my Spanish studies by automatically creating Anki cards from a text file.

It's a project to make studying smarter, not harder.

## Features (v1.0)

*   Reads sentences from a `frases.txt` file (format: `front|back`).
*   Generates audio for the front of the card using Google Text-to-Speech.
*   Adds the card (text + audio) to a specified Anki deck automatically.
*   Uses a limit to control how many cards are added per run.

## Tech Stack

*   **Python 3**
*   **AnkiConnect:** The bridge that allows the script to communicate with the Anki desktop app.
*   **requests:** To send data to the AnkiConnect API.
*   **gTTS:** To generate audio from text.

## Setup

1.  Clone the repository.
2.  Create and activate a virtual environment: `python -m venv venv` and `source venv/bin/activate`.
3.  Install dependencies: `pip install -r requirements.txt`.
4.  Make sure Anki is running with the AnkiConnect plugin installed.
5.  Run the script: `python anki_automator.py`.

text file