import requests
import time
from video_translation_server import VideoTranslationServer
from fastapi import FastAPI, Request
import threading
import uvicorn
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VideoTranslationClient:
    def __init__(self, server_url: str, webhook_host: str, webhook_port: str) -> None:
        self.server_url = server_url
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
                logging.info(f"Received status from webhook. Status: " + self.latest_status)
            return {"message": "Update received"}

        thread = threading.Thread(target=self.run_webhook_server)
        thread.daemon = True
        thread.start()

    def run_webhook_server(self):
        uvicorn.run(self.app, host=self.webhook_host, port=self.webhook_port)

    def register_webhook(self):
        callback_url = f"http://{self.webhook_host}:{self.webhook_port}/webhook"
        try:
            response = requests.post(f"{self.server_url}/register_webhook", data={'webhook_url': callback_url})
            response.raise_for_status()
            logging.info(f"Webhook registered. Listening for updates at {callback_url}")

            # Immediate check of current job status after webhook registration, edge case where it's still pending on creation
            current_status_response = requests.get(f"{self.server_url}/status")
            current_status_response.raise_for_status()
            current_status = current_status_response.json().get("status", "pending")

            self.latest_status = current_status
            logging.info(f"Immediately fetched current job status: {self.latest_status}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to register webhook: {e}")

    def get_job_status(self):
        return self.latest_status


if __name__ == "__main__":

    client = VideoTranslationClient(
        server_url="http://localhost:8000", webhook_host="localhost", webhook_port=5000,
    )

    client.register_webhook()

    while client.get_job_status() == "pending":
        logging.info(
            f"Job status: {client.get_job_status()} (waiting for update from server...)"
        )
        time.sleep(2)

    logging.info(f"Final job status: {client.get_job_status()}")
