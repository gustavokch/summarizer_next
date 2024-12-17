Here's a complete **README.md** for your app:

---

# Video Transcription and Summarization API

This FastAPI-based application allows users to transcribe and summarize YouTube videos. It extracts audio, transcribes it using Google's Gemini API, and generates a summarized version of the transcription. The results are stored in a local SQLite database.

## Features

- **YouTube Video Support**: Extracts audio from YouTube and other services videos using `yt-dlp`.
- **Audio Transcription**: Uses Google's Generative AI (`google-generativeai`) for transcription.
- **Summarization**: Summarizes transcriptions to concise outputs.
- **Session Management**: Tracks user tasks via session cookies.
- **Database Persistence**: Stores transcriptions and summaries in SQLite.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Dependencies](#dependencies)
- [Notes](#notes)

---

## Getting Started

To get this API running on your local machine, follow the steps below.

---

## Prerequisites

- **Python 3.9+**
- **pip** for managing dependencies
- A Google API Key for using the **Generative AI** API.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/gustavokch/summarizer_next
   cd summarizer_next
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

Create a `.env` file in the project directory with the following:

```env
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
UPLOAD_DIRECTORY="./uploads"
DATABASE_URL="sqlite:///./transcription_db.sqlite"
GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_CLIENT_SECRET"
```

Replace placeholder values with your actual Google API credentials.

---

## Running the Application

Run the FastAPI server using `uvicorn`:

```bash
uvicorn app:app --host 0.0.0.0 --port 8090 --reload
```

- The API will be available at: `http://localhost:8090`.

---

## API Endpoints

### 1. Transcribe YouTube Video

**Request**:  
- **POST** `/transcribe`
- **Payload**:
  ```json
  {
    "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID"
  }
  ```

**Response**:
```json
{
  "task_id": "1",
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "video_title": "Sample Video Title",
  "transcription": "Full transcription text...",
  "summary": "Summarized transcription..."
}
```

---

### 2. Get All User Tasks

**Request**:  
- **GET** `/tasks`

**Response**:
```json
[
  {
    "task_id": "1",
    "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "video_title": "Sample Video Title",
    "transcription": "Full transcription text...",
    "summary": "Summarized transcription..."
  }
]
```

---

### 3. Delete a Task

**Request**:  
- **DELETE** `/tasks/{task_id}`

**Response**:
```json
{
  "message": "Task deleted successfully"
}
```

---

## Dependencies

This app uses the following key libraries:

- **FastAPI**: Backend framework.
- **yt-dlp**: Download YouTube video audio.
- **Google Generative AI**: Audio transcription and summarization.
- **SQLAlchemy**: Database ORM.
- **Pydantic**: Data validation.
- **Uvicorn**: ASGI server for FastAPI.

All dependencies are listed in [requirements.txt](./requirements.txt).

---

## Notes

1. **Google Generative AI**: Ensure you have access to the API and the necessary keys configured in `.env`.
2. **File Management**: Audio files are stored in the `./uploads` directory.
3. **Session Handling**: Cookies are used to persist user tasks across sessions.

---

## License

This project is licensed under the MIT License.
