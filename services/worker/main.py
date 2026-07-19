import time, signal, sys
from dotenv import load_dotenv
from services.agent.main import process_task_queue

load_dotenv()
# ... (signal handling remains the same)

def run():
    print("Worker active. Monitoring for Business & Tech growth...")
    while running:
        try: process_task_queue()
        except Exception as e: print(f"Worker error: {e}")
        time.sleep(300) 

if __name__ == "__main__": run()