from fastapi import FastAPI
import uvicorn
import asyncio
import random


class VideoTranslationServer:
    def __init__(
        self,
        error_probability: float = 0.1,
        length_of_translation: int = 100
    ) -> None:
        self.app = FastAPI()
        self.video_status = "pending"
        self.error_probability = error_probability
        self.length_of_translation = length_of_translation
        self.start_time = 0

        self._initialize_routes()
        self.app.add_event_handler("startup", self.start_translation)

    def _initialize_routes(self):
        @self.app.get("/status")
        async def status():
            return {"result": self.video_status}

    async def start_translation(self):
        asyncio.create_task(self.simulate_translation())
    
    async def simulate_translation(self):
        self.start_time = asyncio.get_event_loop().time()
        while self.video_status == "pending":
            elapsed_time = asyncio.get_event_loop().time() - self.start_time
            if elapsed_time >= self.length_of_translation:
                if random.random() < self.error_probability:
                    self.video_status = "error"
                else:
                    self.video_status = "completed"
                print(self.video_status)
                break
            await asyncio.sleep(1)


if __name__ == "__main__":
    server = VideoTranslationServer()
    app = server.app
    uvicorn.run(app, host="0.0.0.0", port=8000)
