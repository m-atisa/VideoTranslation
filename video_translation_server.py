from fastapi import FastAPI, HTTPException, Form, BackgroundTasks
import asyncio
import random
import uvicorn
import requests
import logging
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class VideoTranslationServer:
    def __init__(
        self, error_probability: float = 0.1, length_of_translation: int = 100
    ) -> None:
        self.app = FastAPI(lifespan=self.lifespan)
        self.video_status = "pending"
        self.webhook_url = None
        self.notification_sent = False
        self.translation_started = False
        self.error_probability = error_probability
        self.length_of_translation = length_of_translation
        self.webhook_registered_event = None
        self._initialize_routes()

    def _initialize_routes(self):
        @self.app.get("/status")
        async def status():
            logging.info(f"Client requested current job status: {self.video_status}")
            return {"status": self.video_status}

        @self.app.post("/register_webhook")
        async def register_webhook(
            background_tasks: BackgroundTasks, webhook_url: str = Form(...)
        ):
            logging.info("Received webhook URL: " + webhook_url)
            if not webhook_url:
                raise HTTPException(status_code=400, detail="Invalid webhook URL")

            # Update the webhook URL
            self.webhook_url = webhook_url
            self.webhook_registered_event.set()

            # If translation has finished, notify the client immediately, but only if notification was not already sent
            if self.video_status != "pending" and not self.notification_sent:
                logging.info(f"Translation already ended with '{self.video_status}'. Sending status to new webhook.")
                background_tasks.add_task(self.send_webhook_notification, self.video_status)
            elif self.video_status == "pending":
                logging.info("Translation is still in progress.")
            return {"message": "Webhook registered"}

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        logging.info("Lifespan started, initializing translation simulation...")
        self.webhook_registered_event = asyncio.Event()
        asyncio.create_task(self.simulate_translation())
        yield

    async def send_webhook_notification(self, status: str, retry_attempts: int = 5):
        """Sends the current translation status to the registered webhook, with retry logic."""
        if not self.webhook_url:
            logging.info(f"No webhook registered to notify status: {status}.")
            return

        if self.notification_sent:
            logging.info(f"Notification already sent. No further attempts necessary for status: '{status}'.")
            return
        else:
            for attempt in range(1, retry_attempts + 1):
                try:
                    logging.info(f"Attempting to send webhook notification (Attempt {attempt}/{retry_attempts})...")
                    response = requests.post(self.webhook_url, json={"status": status})

                    if response.status_code == 200:
                        logging.info(f"Webhook notification sent successfully. Status: '{status}'")
                        self.notification_sent = True
                        break
                    else:
                        logging.error(f"Failed to send webhook. Status code: {response.status_code}")

                except Exception as e:
                    logging.error(f"Error during webhook notification: {e}")

                await asyncio.sleep(2 * attempt)

        if not self.notification_sent:
            logging.error("Failed to send webhook notification after multiple attempts.")

    async def simulate_translation(self):
        """Simulates translation processed in the background when the server starts."""
        self.translation_started = True
        self.start_time = int(asyncio.get_event_loop().time())
        logging.info("Translation simulation started.")

        while self.video_status == "pending":
            elapsed_time = int(asyncio.get_event_loop().time()) - self.start_time
            if elapsed_time >= self.length_of_translation:
                self.video_status = (
                    "error" if random.random() < self.error_probability else "completed"
                )
                logging.info(f"Translation finished with status: {self.video_status}")

                # Wait for webhook registration if not already registered
                if not self.webhook_url:
                    logging.info(f"Waiting for webhook registration to notify final status: {self.video_status}")
                    await self.webhook_registered_event.wait()  # Wait until the webhook is registered

                # Only send the notification if not already sent
                if not self.notification_sent:
                    await self.send_webhook_notification(self.video_status)

                break

            await asyncio.sleep(1)

        logging.info("Translation simulation ended.")


if __name__ == "__main__":
    server = VideoTranslationServer(error_probability=0.1, length_of_translation=20)

    app = server.app
    uvicorn.run(app, host="0.0.0.0", port=8000)
