from fastapi import FastAPI
import uvicorn
import asyncio
import random

class VideoTranslationServer:
    def __init__(self, min_delay: int = 0, max_delay: int = 0, error_probability: float = .1) -> None:
        self.app = FastAPI()
        self.video_status = "pending"
        self.delay_amount = random.uniform(min_delay, max_delay)
        self.error_probability = error_probability
        self._initialize_routes()

    def _initialize_routes(self) -> None:
        @self.app.get("/status")
        def status():
            return {"result": self.video_status}
        
    async def simulate_translation(self):
        if random.random() < self.error_probability:
            self.video_status = "error"
        else: 
            self.video_status = "completed"


server = VideoTranslationServer()
app = server.app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
