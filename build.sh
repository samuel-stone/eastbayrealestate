#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- Installing Python dependencies from requirements.txt ---"
pip install -r requirements.txt

echo "--- Installing Playwright Chromium system dependencies and binaries ---"
playwright install chromium
playwright install-deps chromium

echo "--- Build complete! ---"