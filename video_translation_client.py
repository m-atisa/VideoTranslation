import requests
import time


class VideoTranslationClient:
    def __init__(self, server_url: str, polling_interval: int = 5) -> None:
        self.server_url = server_url
        self.polling_interval = polling_interval

    def _make_get_request(self):
        try:
            response = requests.get(f"{self.server_url}/status")
            return response.json()
        except:
            print("Failed to retrieve status")

    def get_status(self):
        status_response = self._make_get_request()
        status = status_response.get("result", "error")

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
