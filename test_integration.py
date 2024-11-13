import pytest
import requests
from multiprocessing import Process
from time import sleep
import uvicorn
from video_translation_server import VideoTranslationServer
from video_translation_client import VideoTranslationClient
import threading
import logging
import socket

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def start_server(port):
    """ Start the FastAPI server with Uvicorn on a specific port """
    server = VideoTranslationServer(error_probability=0.1, length_of_translation=20)
    uvicorn.run(server.app, host="0.0.0.0", port=port, log_level="info")

@pytest.fixture(scope="session", autouse=True)
def run_server():
    """ Fixture to run the server in the background. Automatically started with pytest session. """
    server_process = Process(target=start_server, args=(8000,), daemon=True)
    server_process.start()
    
    sleep(2)

    server_url = f"http://localhost:8000/status"
    try:
        response = requests.get(server_url)
        assert response.status_code == 200, "Server did not start correctly"
        logging.info(f"Server started successfully on port 8000")
    except Exception as e:
        server_process.terminate()
        pytest.fail(f"Server did not start: {e}")
    
    yield
    
    server_process.terminate()
    server_process.join()

@pytest.fixture(scope="session")
def run_client():
    """ Fixture to start the client's webhook server on a dynamic port. """
    webhook_port = 3120
    logging.info(f"Starting client webhook on port: {webhook_port}")
    
    client = VideoTranslationClient(
        webhook_host="localhost",
        webhook_port=webhook_port
    )

    # Start the client webhook server in an independent thread
    thread = threading.Thread(target=client.run_webhook_server, daemon=True)
    thread.start()
    
    sleep(1)
    yield client
    thread.join(1)

@pytest.mark.parametrize("endpoint", ["/status"])
def test_server_status_endpoint(endpoint):
    url = f"http://localhost:8000{endpoint}"
    response = requests.get(url)
    assert response.status_code == 200, f"Failed to access {endpoint}"
    assert response.json()["status"] == "pending", f"Unexpected job status in {endpoint}"

def send_webhook_update(client, status):
    url = f"http://{client.webhook_host}:{client.webhook_port}/webhook"
    data = {"status": status}
    return requests.post(url, json=data)

def test_webhook_integration(run_client):
    client = run_client

    response = client.register_webhook()
    logging.info(f"Client registered webhook: {response}")

    initial_status = client.get_job_status()
    assert initial_status == "pending", f"Initial job status was '{initial_status}', expected 'pending'."

    webhook_response = send_webhook_update(client, "error")
    assert webhook_response.status_code == 200, "Failed to send 'error' webhook update."
    
    sleep(1)
    
    updated_status = client.get_job_status()
    assert updated_status == "error", f"Expected 'error', got '{updated_status}'"

    webhook_response = send_webhook_update(client, "completed")
    assert webhook_response.status_code == 200, "Failed to send 'completed' webhook update."

    sleep(1)
    
    final_status = client.get_job_status()
    assert final_status == "completed", f"Expected 'completed', got '{final_status}'"
