from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import random


class VideoTranslationServer:
    def __init__(
        self, min_delay: int = 0, max_delay: int = 0, error_probability: float = 0.1
    ) -> None:
        self.app = FastAPI(lifespan=self.lifespan)
        self.video_status = "pending"
        self.delay_amount = random.uniform(min_delay, max_delay)
        self.error_probability = error_probability

        self._initialize_routes()

    def _initialize_routes(self):
        @self.app.get("/status")
        async def status():
            return {"result": self.video_status}

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        await asyncio.create_task(self.simulate_translation())
        yield

    async def simulate_translation(self):
        await asyncio.sleep(self.delay_amount)
        if random.random() < self.error_probability:
            self.video_status = "error"
        else:
            self.video_status = "completed"


if __name__ == "__main__":
    server = VideoTranslationServer(min_delay=7, max_delay=8)
    app = server.app
    uvicorn.run(app, host="0.0.0.0", port=8000)
