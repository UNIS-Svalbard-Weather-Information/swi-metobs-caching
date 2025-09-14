#!/bin/bash

REPO_URL="https://github.com/UNIS-Svalbard-Weather-Information/swi-metobs-station-configuration.git"
FOLDER_NAME="config"

# Save the initial directory
INITIAL_DIR=$(pwd)

if [ -d "$FOLDER_NAME" ]; then
    # If the folder exists, pull the latest changes
    echo "Folder '$FOLDER_NAME' exists. Pulling the latest changes..."
    cd "$FOLDER_NAME" || exit
    git pull origin main
    # Return to the initial directory
    cd "$INITIAL_DIR" || exit
else
    # If the folder does not exist, clone the repository
    echo "Folder '$FOLDER_NAME' does not exist. Cloning the repository..."
    git clone "$REPO_URL" "$FOLDER_NAME"
fi


python3 ./run.py