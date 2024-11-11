import requests
import time
from video_translation_server import VideoTranslationServer

class VideoTranslationClient:
    def __init__(self, server_url: str, 
                 polling_interval: int = 5,
                 max_retries: int = 5) -> None:
        self.server_url = server_url
        self.polling_interval = polling_interval
        self.max_retries = max_retries

    def _make_get_request(self):
        for i in range(1, self.max_retries + 1):
            try:
                response = requests.get(f"{self.server_url}/status")
                return response.json()
            except requests.exceptions.RequestException as e:
                wait_time = i
                time.sleep(wait_time)
                print(f"Failed to retrieve status trying again in {wait_time} seconds.")
        raise RuntimeError(f"Failed to reach the server after {self.max_retries} attempts")

    def get_status(self):
        status_response = self._make_get_request()
        status = status_response.get("result", "error")
        while status == "pending":
            if status == "completed":
                print("Video translation is completed")
            elif status == "error":
                print("An error occurred during the video translation process")
            else:
                print(
                    "Translation is still pending, cheking again in "
                    + str(self.polling_interval)
                    + " seconds"
                )
                time.sleep(self.polling_interval)

if __name__ == "__main__":
    client = VideoTranslationClient(server_url="http://localhost:8000", polling_interval=5)
    client.get_status()