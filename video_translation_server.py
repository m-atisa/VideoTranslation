from fastapi import FastAPI
import uvicorn

class VideoTranslationServer:
    def __init__(self, delay_amount: int = 0) -> None:
        self.app = FastAPI()
        self.video_status = "pending"
        self.delay_amount = delay_amount
        self._initialize_routes()

    def _initialize_routes(self) -> None:
        @self.app.get("/status")
        def status():
            return {"Hello": "World"}


server = VideoTranslationServer()
app = server.app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
