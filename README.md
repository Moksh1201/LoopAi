# Data Ingestion API System

A RESTful API system for handling data ingestion requests with priority-based processing and rate limiting.

## Features

- Asynchronous batch processing of data ingestion requests
- Priority-based request processing (HIGH, MEDIUM, LOW)
- Rate limiting (1 batch per 5 seconds)
- Batch size limit (3 IDs per batch)
- Status tracking for ingestion requests
- Input validation for IDs (range: 1 to 10^9+7)

## API Endpoints

### 1. Ingestion API
- **Endpoint**: `POST /ingest`
- **Input**: JSON payload with IDs and priority
  ```json
  {
    "ids": [1, 2, 3, 4, 5],
    "priority": "HIGH"
  }
  ```
- **Output**: JSON response with ingestion ID
  ```json
  {
    "ingestion_id": "abc123"
  }
  ```

### 2. Status API
- **Endpoint**: `GET /status/<ingestion_id>`
- **Input**: Ingestion ID from the ingestion API
- **Output**: JSON response with status and batch details
  ```json
  {
    "ingestion_id": "abc123",
    "status": "triggered",
    "batches": [
      {
        "batch_id": "uuid1",
        "ids": [1, 2, 3],
        "status": "completed"
      },
      {
        "batch_id": "uuid2",
        "ids": [4, 5],
        "status": "triggered"
      }
    ]
  }
  ```

## Status Values

### Batch Status
- `yet_to_start`: Batch hasn't started processing
- `triggered`: Batch is currently being processed
- `completed`: Batch processing is complete

### Overall Status
- `yet_to_start`: All batches are yet to start
- `triggered`: At least one batch is triggered
- `completed`: All batches are completed

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   uvicorn app:app --reload
   ```

## Running Tests

```bash
pytest test_app.py -v
```

## Docker Support

Build and run using Docker:

```bash
docker-compose up --build
```

## Design Choices

1. **FastAPI**: Chosen for its modern async support, automatic OpenAPI documentation, and type checking.
2. **In-memory Storage**: Using in-memory dictionaries for simplicity. In production, this would be replaced with a database.
3. **Priority Queue**: Using Python's heapq for efficient priority-based processing.
4. **Async Processing**: Using asyncio for non-blocking I/O and efficient resource utilization.
5. **Rate Limiting**: Implemented using asyncio.sleep to ensure batches are processed at the required rate.

## Rate Limiting

- Maximum 3 IDs processed at any time
- One batch processed every 5 seconds
- Higher priority requests are processed before lower priority ones
- Within the same priority, requests are processed in FIFO order

## Error Handling

- Input validation for IDs (range: 1 to 10^9+7)
- Validation for required fields
- Proper error responses for invalid inputs
- 404 responses for non-existent ingestion IDs 