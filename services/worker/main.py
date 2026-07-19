import time
from services.agent.main import process_task_queue

print("Worker persistent loop initialized...")

if __name__ == "__main__":
    while True:
        try:
            process_task_queue()
        except Exception as e:
            print(f"Worker Loop Error: {e}")
        # Wait 15 seconds between polling to save CPU
        time.sleep(15)