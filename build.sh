#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Ensure FFmpeg is available (imageio-ffmpeg usually handles this, 
# but this script can be expanded for other system dependencies)
