#!/bin/bash

REPO_URL="https://github.com/UNIS-Svalbard-Weather-Information/swi-metobs-station-configuration.git"
FOLDER_NAME="config"

if [ -d "$FOLDER_NAME" ]; then
    # If the folder exists, pull the latest changes
    echo "Folder '$FOLDER_NAME' exists. Pulling the latest changes..."
    cd "$FOLDER_NAME" || exit
    git pull origin main
else
    # If the folder does not exist, clone the repository
    echo "Folder '$FOLDER_NAME' does not exist. Cloning the repository..."
    git clone "$REPO_URL" "$FOLDER_NAME"
fi
