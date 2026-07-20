import os
import requests
import json
from datetime import datetime

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

def generate_analytics_notebook():
    """Asks Llama to generate a complete Pandas/Plotly data analysis script and structures it into a Jupyter Notebook JSON format."""
    
    prompt = (
        "You are an expert Data Science Analytics Architect. "
        "Generate a Python script for a Jupyter notebook that connects to a PostgreSQL database using pandas and psycopg2, "
        "queries real estate permit tables (leads, prospect_features), "
        "and builds a Plotly scatter geo-cluster or momentum histogram. "
        "Return ONLY valid raw JSON representing a Jupyter Notebook (.ipynb structure with 'cells' containing code and markdown cells). "
        "Do not include markdown code block ticks like ```json, just output the raw JSON object."
    )

    try:
        payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code == 200:
            raw_text = response.json().get("response", "")
            clean_json = raw_text.replace("```json", "").replace("```", "").strip()
            notebook_data = json.loads(clean_json)
            
            filename = f"generated_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ipynb"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(notebook_data, f, indent=2)
            return filename
    except Exception as e:
        print(f"Error generating notebook via LLM: {e}")

    # Fallback standard notebook template if local gen fails
    fallback_nb = {
      "cells": [
       {
        "cell_type": "markdown",
        "metadata": {},
        "source": ["# East Bay Real Estate Analytics\n", "Auto-generated exploration notebook."]
       },
       {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
         "import os\n",
         "import pandas as pd\n",
         "import psycopg2\n",
         "import plotly.express as px\n\n",
         "conn = psycopg2.connect(os.environ['DATABASE_URL'])\n",
         "df = pd.read_sql('SELECT * FROM prospect_features LIMIT 100', conn)\n",
         "conn.close()\n",
         "df.head()"
        ]
       }
      ],
      "metadata": {
       "language_info": {"name": "python"}
      },
      "nbformat": 4,
      "nbformat_minor": 2
    }
    
    filename = "fallback_analytics_notebook.ipynb"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(fallback_nb, f, indent=2)
    return filename

if __name__ == "__main__":
    nb = generate_analytics_notebook()
    print(f"Generated notebook: {nb}")