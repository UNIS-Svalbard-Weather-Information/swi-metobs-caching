#!/bin/bash

REPO_URL="https://github.com/UNIS-Svalbard-Weather-Information/swi-metobs-station-configuration.git"
FOLDER_NAME="config"
OTHER_CONFIG="/swi/data/__swi-config__"

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


# Create the target directory if it does not exist
if [ ! -d "$OTHER_CONFIG" ]; then
    echo "Creating directory '$OTHER_CONFIG'..."
    mkdir -p "$OTHER_CONFIG" || exit 1
fi

# Copy files from the repository to the target directory, overwriting existing files
echo "Copying files from '$FOLDER_NAME' to '$OTHER_CONFIG' (overwriting existing files)..."
cp -rf "$FOLDER_NAME"/* "$OTHER_CONFIG/" || exit 1

# Run the Python script
echo "Running run.py..."
python3 ./run.py
