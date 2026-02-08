#!/bin/bash

# Ensures the script is run from its own directory
cd "$(dirname "$0")"

echo "--- Starting automated process ---"

# 1. Check if Anki is running
if ! pgrep -x "anki" > /dev/null; then
    echo "Anki is not running. Starting Anki in the background..."
    anki &

    echo "Waiting 15 seconds for Anki and AnkiConnect to start..."
    sleep 15
else
    echo "Anki is already running. Continuing..."
fi

# Check if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment directory 'venv' not found."
    echo "Please create it with: python -m venv venv"
    exit 1
fi

# 2. Activate the virtual environment and run the Python script
echo "Activating virtual environment and running card insertion script..."
source venv/bin/activate
python anki_automator.py

echo "--- Process finished ---"