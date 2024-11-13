# HeyGen - Video Translation Project

## Overview

For my implementation of the video translation project, I've written code to facilitate communication between a **Server**—responsible for handling video translation jobs—and a **Client**—which registers webhooks to receive updates on the status of those translation requests. The initial naive approach of simply querying the server posed several issues.

### Downsides to naive approach
1. Excessive polling of the server could degrade performance and increase instability.
2. Infrequent polling could lead to delay in customers knowing when translation is done.
3. Redundant status checking, majority of the requests to check status will be 'pending'.
4. Customers forced to handle logic regarding when to query server when making api calls.

### Upside to webhook approach
Based on these considerations I opted to used webhooks to improve the service. 
1. Since webhooks are event driven there is much lower server load.
2. Client notified as soon as translation job is done.
3. Better for scalability as the server can handle more load.
4. Clients don't have to poll and simply receive updates for greater simplicity.
   

## Server Code: `VideoTranslationServer`

The server is responsible for:

1. **Receiving new video translation requests** and simulating the translation process.
2. **Sending status updates** via registered webhooks as the translation progresses.

### Key Features:

- Processes video translation requests and posts updates to the client’s webhook.
- Provides the current translation job status through an API endpoint (`/status`).
  
### Architecture

- **Server URL**: The server listens on `localhost:8000`.
- **Webhook Callbacks**: The server sends updates such as `pending`, `completed`, or `error` to the registered webhook URL.
- **Status Endpoint**: Accessible via `GET /status`, the server provides the current translation job status.

---

## Client Code: `VideoTranslationClient`

The **Client** is responsible for:

1. **Registering a webhook** with the server to receive status updates related to the video translation process.
2. **Running a FastAPI Webhook server**, which listens for status updates and reflects them in the client.
3. **Handling incoming webhook status updates** and updating the job status accordingly.

### Key Features:

- **Webhook Registration**: Registers the client's webhook URL with the Video Translation Server. The server will send job status updates to this URL.
- **Webhook Handling**: Spins up a FastAPI application that listens for POST requests from the server to update the job status.
- **Thread Management**: Runs the webhook server in a separate thread to allow asynchronous communication with the server.
- **Immediate Status Fetch**: After webhook registration, the client fetches the current job status from the server to handle cases where the job is already progressing.

---

## How to Use the Client Code

1. Initialize the client
```bash
client = VideoTranslationClient(webhook_host="localhost", webhook_port=3120)
```
2. Register webhook with server
```bash
client.register_webhook()
```
Once the webhook is registered the server will automatically notify the client when the translation is in a `completed` or `error` state.

### Prerequisites:

First create a new environment to install packages into

```bash
python -m venv myenv
```
To activate the environment do the following.
If you're in windows 
  ```myenv\Scripts\activate```
otherwise if you're using linux use
  ```source myenv/bin/activate```

Ensure you have the dependencies installed:

```bash
pip install -r requirements.txt
```

## Running Integration Tests
As part of the requirements I wrote integration tests to validate the interaction between the server and client to ensure it behaves as designed.
The file tests the following.
1. Server can be successfully started and accessed.
2. Client can register a webhook and receive status updates from the server.
3. Webhooks function correctly, sending notifications to the client when the job status changes (e.g., from pending to error or completed).

Running the test with no logs
```
> pytest -p no:warnings test_integration.py   
========================================================================== test session starts ==========================================================================
platform win32 -- Python 3.8.5, pytest-8.3.3, pluggy-1.5.0
rootdir: C:\Users\matis\Desktop\VideoTranslation
plugins: anyio-4.5.2
collected 2 items

test_integration.py ..                                                                                                                                             [100%]

========================================================================== 2 passed in 16.54s ===========================================================================
```
Running the tests with logs
```
> pytest -p no:warnings -s test_integration.py
========================================================================== test session starts ==========================================================================
platform win32 -- Python 3.8.5, pytest-8.3.3, pluggy-1.5.0
rootdir: C:\Users\matis\Desktop\VideoTranslation
plugins: anyio-4.5.2
collected 2 items

test_integration.py INFO:     Started server process [21560]
INFO:     Waiting for application startup.
2024-11-13 08:57:42,798 - INFO - Lifespan started, initializing translation simulation...
2024-11-13 08:57:42,798 - INFO - Translation simulation started.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
2024-11-13 08:57:45,651 - INFO - Client requested current job status: pending
INFO:     127.0.0.1:4758 - "GET /status HTTP/1.1" 200 OK
2024-11-13 08:57:47,692 - INFO - Client requested current job status: pending
INFO:     127.0.0.1:4760 - "GET /status HTTP/1.1" 200 OK
.INFO:     Started server process [19440]
INFO:     Started server process [19440]
INFO:     Waiting for application startup.
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Application startup complete.
..
..
..
===================================================================== 2 passed, 1 warning in 14.23s =====================================================================
```
