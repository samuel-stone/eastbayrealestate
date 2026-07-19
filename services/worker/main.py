import time
import signal
import sys
from dotenv import load_dotenv
from services.agent.main import process_task_queue

load_dotenv()

# Define the global control variable
running = True

def shutdown_handler(signum, frame):
    global running
    print("\nWorker shutdown requested.")
    running = False

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

def run():
    global running # Ensure the function can see the global 'running'
    print("Worker active. Monitoring for Business & Tech growth...")
    
    while running:
        try:
            process_task_queue()
        except Exception as e:
            print(f"Worker heartbeat error: {e}")
        
        # Short sleep to prevent CPU spiking while keeping loop responsive
        time.sleep(300) 
        
    print("Worker stopped cleanly.")
    sys.exit(0)

if __name__ == "__main__":
    run()