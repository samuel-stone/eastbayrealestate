import time
import sys
import os

# Add the project root to sys.path so we can import 'services'
sys.path.append(os.getcwd())

from services.agent.main import process_task_queue 

def run():
    print("Worker started. Monitoring ai_tasks...")
    while True:
        process_task_queue()
        time.sleep(60)

if __name__ == "__main__":
    run()