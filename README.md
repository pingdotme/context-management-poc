
# Meeting Context API

A FastAPI service that stores and retrieves meeting notes with semantic search capabilities.

## Features
- Semantic search for related meeting context
- Automatic meeting categorization
- Duplicate detection
- Meeting history with filtering
- Export functionality

## API Endpoints

### Store Meeting
```http
POST /process-meeting
```

**Request Body:**
```json
{
  "user_id": "string",
  "meeting_text": "string",
  "categories": ["api", "security", "review", "planning"]  // optional
}
```

**Response:**
```json
{
  "summary": "string",
  "context_used": [
    {
      "meeting_id": "string",
      "text": "string",
      "timestamp": "string",
      "categories": ["string"],
      "similarity_score": 0.0
    }
  ],
  "timestamp": "string",
  "context_count": 0
}
```

### Get Meeting History
```http
GET /meetings/{user_id}/history
```

**Parameters:**
- `user_id` (path) - User ID
- `limit` (query) - Max results to return (default: 10, max: 100)
- `skip` (query) - Number of results to skip (default: 0)
- `categories` (query) - Filter by categories (optional)
- `search_text` (query) - Search in meeting text (optional)
- `start_date` (query) - Filter by start date (ISO format)
- `end_date` (query) - Filter by end date (ISO format)

**Response:**
```json
{
  "meetings": [
    {
      "meeting_id": "string",
      "text": "string",
      "timestamp": "string",
      "categories": ["string"],
      "similarity_score": null
    }
  ],
  "total": 0,
  "skip": 0,
  "limit": 10,
  "filtered_total": 0
}
```

### Delete Meeting
```http
DELETE /meetings/{user_id}/{meeting_id}
```

**Parameters:**
- `user_id` (path) - User ID
- `meeting_id` (path) - Meeting ID

**Response:**
```json
{
  "status": "success",
  "message": "string"
}
```

### Cleanup Duplicates
```http
POST /meetings/{user_id}/cleanup
```

**Parameters:**
- `user_id` (path) - User ID

**Response:**
```json
{
  "status": "success",
  "removed_count": 0,
  "message": "string"
}
```

### Export Meetings
```http
GET /meetings/{user_id}/export
```

**Parameters:**
- `user_id` (path) - User ID
- `start_date` (query) - Filter by start date (ISO format)
- `end_date` (query) - Filter by end date (ISO format)
- `categories` (query) - Filter by categories (optional)

**Response:**
Downloads a JSON file containing:
```json
{
  "user_id": "string",
  "meetings": [
    {
      "meeting_id": "string",
      "text": "string",
      "timestamp": "string",
      "categories": ["string"],
      "similarity_score": null
    }
  ],
  "export_date": "string",
  "total_meetings": 0
}
```

## Categories
Available meeting categories:
- `api` - API-related discussions
- `security` - Security-related topics
- `planning` - Planning meetings
- `review` - Review sessions
- `other` - Uncategorized meetings

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
uvicorn app.main:app --reload
```

## Environment Variables
- `CHROMA_DATA_DIR` - Directory for ChromaDB storage (default: "data/vector_store")
- `LOG_LEVEL` - Logging level (default: "INFO")

## Docker
```bash
# Build
docker build -t meeting-context-api .

# Run
docker run -p 8000:8000 meeting-context-api
```

## Example Usage

Store a meeting:
```bash
curl -X POST "http://localhost:8000/process-meeting" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "user123",
       "meeting_text": "API security review meeting",
       "categories": ["api", "security", "review"]
     }'
```

Get meeting history:
```bash
curl "http://localhost:8000/meetings/user123/history?categories=security&limit=5"
```

Export meetings:
```bash
curl "http://localhost:8000/meetings/user123/export?start_date=2024-01-01T00:00:00"
```
