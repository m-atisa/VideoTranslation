import requests
import time
from video_translation_server import VideoTranslationServer
from fastapi import FastAPI, Request
import threading
import uvicorn
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VideoTranslationClient:
    def __init__(self, webhook_host: str, webhook_port: str) -> None:
        self.server_url = f"http://localhost:8000"

        self.webhook_host = webhook_host
        self.webhook_port = webhook_port
        self.latest_status = "pending"
        self.app = FastAPI()
        
        @self.app.post("/webhook")
        async def receive_webhook(request: Request):
            data = await request.json()
            status = data.get("status")
            if status:
                self.latest_status = status
                logging.info(f"Received status from webhook. Status: {self.latest_status}")
            return {"message": "Update received"}
        
        # Start the webhook server in a separate thread during initialization.
        thread = threading.Thread(target=self.run_webhook_server)
        thread.daemon = True
        thread.start()

    def run_webhook_server(self):
        uvicorn.run(self.app, host=self.webhook_host, port=self.webhook_port)

    def register_webhook(self):
        """Register client's webhook URL with the translation server."""
        callback_url = f"http://{self.webhook_host}:{self.webhook_port}/webhook"
        try:
            response = requests.post(f"{self.server_url}/register_webhook", data={'webhook_url': callback_url})
            response.raise_for_status()
            logging.info(f"Webhook registered. Listening for updates at {callback_url}")
            
            # Fetch the current job status immediately upon webhook registration, edge case where job is stil pending otherwise
            current_status_response = requests.get(f"{self.server_url}/status")
            current_status_response.raise_for_status()
            current_status = current_status_response.json().get("status", "pending")

            self.latest_status = current_status
            logging.info(f"Immediately fetched current job status: {self.latest_status}")
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to register webhook: {e}")

    def get_job_status(self):
        return self.latest_status
