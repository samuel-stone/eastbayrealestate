#!/bin/bash
echo "🚀 Starting East Bay Real Estate AI Platform..."

# Check if Ollama is running, start if available
if command -v ollama &> /dev/null; then
    echo "🤖 Starting local Ollama service..."
    ollama serve &
    sleep 2
else
    echo "⚠️ Ollama CLI not detected locally. Running in Safe Fallback Mode."
fi

# Launch Streamlit Dashboard
echo "🏡 Launching Streamlit dashboard..."
streamlit run app.py