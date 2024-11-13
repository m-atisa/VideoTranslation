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

def find_free_port():
    """ Find and return a free port """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def start_server(server_port):
    """ Start the FastAPI server with Uvicorn on a specific port """
    server = VideoTranslationServer(error_probability=0.1, length_of_translation=20)
    uvicorn.run(server.app, host="0.0.0.0", port=server_port, log_level="info")

@pytest.fixture(scope="session", autouse=True)
def run_server():
    """ Fixture to run the server in the background. Automatically started with pytest session. """
    global SERVER_PORT
    SERVER_PORT = find_free_port()
    server_process = Process(target=start_server, args=(SERVER_PORT,), daemon=True)
    server_process.start()
    
    sleep(2)
    server_url = f"http://localhost:{SERVER_PORT}/status"

    try:
        response = requests.get(server_url)
        assert response.status_code == 200, "Server did not start correctly"
        logging.info(f"Server started successfully on port {SERVER_PORT}")
    except Exception as e:
        server_process.terminate()
        pytest.fail(f"Server did not start: {e}")
    
    yield
    
    server_process.terminate()
    server_process.join()

@pytest.fixture(scope="session")
def run_client():
    """ Fixture to start the client's webhook server on a dynamic port. """
    webhook_port = find_free_port()
    logging.info(f"Starting client webhook on port: {webhook_port}")
    
    client = VideoTranslationClient(
        server_url=f"http://localhost:{SERVER_PORT}", 
        webhook_host="localhost",
        webhook_port=webhook_port
    )
    
    # Start the client webhook server in a different thread
    thread = threading.Thread(target=client.run_webhook_server, daemon=True)
    thread.start()
    sleep(1)

    yield client

    thread.join(1)

@pytest.mark.parametrize("endpoint", ["/status"])
def test_server_status_endpoint(endpoint):
    """ Test that the server responds correctly on the status endpoint. """
    url = f"http://localhost:{SERVER_PORT}{endpoint}"
    response = requests.get(url)
    
    assert response.status_code == 200, f"Failed to access {endpoint}"
    assert response.json()["status"] == "pending", f"Unexpected job status in {endpoint}"

def send_webhook_update(client, status):
    """ Helper to send a webhook status update to the client. """
    url = f"http://{client.webhook_host}:{client.webhook_port}/webhook"
    data = {"status": status}
    return requests.post(url, json=data)

def test_webhook_integration(run_client):
    """ Test integration between the server and client webhook """
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
