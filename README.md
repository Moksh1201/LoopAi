Data Ingestion API
A simple FastAPI project that accepts a list of IDs, processes them in batches, and lets you check the status of your request.

Features
Accepts list of IDs with priority (HIGH, MEDIUM, LOW)

Splits IDs into batches of 3

Processes 1 batch every 5 seconds

Shows batch and overall status

Validates ID range (1 to 1,000,000,007)

Endpoints
POST /ingest
Input:


{
  "ids": [1, 2, 3],
  "priority": "HIGH"
}
Response:


{
  "ingestion_id": "abc123"
}
GET /status/{ingestion_id}
Response:


{
  "ingestion_id": "abc123",
  "status": "completed",
  "batches": [
    {
      "batch_id": "uuid1",
      "ids": [1, 2, 3],
      "status": "completed"
    }
  ]
}
Status Types
yet_to_start: Not started

triggered: Processing

completed: Done

How to Run

git clone <repo-url>
cd <project-folder>
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
Docker

docker-compose up --build
Tests

