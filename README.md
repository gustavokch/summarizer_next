YouTube Video Transcription and Summarization API
This FastAPI-based application allows users to transcribe and summarize YouTube videos. It extracts audio, transcribes it using Google's Gemini API, and generates a summarized version of the transcription. The results are stored in a local SQLite database.

Features
YouTube Video Support: Extracts audio from YouTube videos using yt-dlp.
Audio Transcription: Uses Google's Generative AI (google-generativeai) for transcription.
Summarization: Summarizes transcriptions to concise outputs.
Session Management: Tracks user tasks via session cookies.
Database Persistence: Stores transcriptions and summaries in SQLite.
Table of Contents
Getting Started
Prerequisites
Installation
Configuration
Running the Application
API Endpoints
Dependencies
Notes
Getting Started
To get this API running on your local machine, follow the steps below.

Prerequisites
Python 3.9+
pip for managing dependencies
A Google API Key for using the Generative AI API.
Installation
Clone the repository:

bash
Copy code
git clone <repository_url>
cd <project_directory>
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Configuration
Create a .env file in the project directory with the following:

env
Copy code
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
UPLOAD_DIRECTORY="./uploads"
DATABASE_URL="sqlite:///./transcription_db.sqlite"
GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_CLIENT_SECRET"
Replace placeholder values with your actual Google API credentials.

Running the Application
Run the FastAPI server using uvicorn:

bash
Copy code
uvicorn app:app --host 0.0.0.0 --port 8090 --reload
The API will be available at: http://localhost:8090.
API Endpoints
1. Transcribe YouTube Video
Request:

POST /transcribe
Payload:
json
Copy code
{
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
Response:

json
Copy code
{
  "task_id": "1",
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "video_title": "Sample Video Title",
  "transcription": "Full transcription text...",
  "summary": "Summarized transcription..."
}
2. Get All User Tasks
Request:

GET /tasks
Response:

json
Copy code
[
  {
    "task_id": "1",
    "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "video_title": "Sample Video Title",
    "transcription": "Full transcription text...",
    "summary": "Summarized transcription..."
  }
]
3. Delete a Task
Request:

DELETE /tasks/{task_id}
Response:

json
Copy code
{
  "message": "Task deleted successfully"
}
Dependencies
This app uses the following key libraries:

FastAPI: Backend framework.
yt-dlp: Download YouTube video audio.
Google Generative AI: Audio transcription and summarization.
SQLAlchemy: Database ORM.
Pydantic: Data validation.
Uvicorn: ASGI server for FastAPI.
All dependencies are listed in requirements.txt.

Notes
Google Generative AI: Ensure you have access to the API and the necessary keys configured in .env.
File Management: Audio files are stored in the ./uploads directory.
Session Handling: Cookies are used to persist user tasks across sessions.
License
This project is licensed under the MIT License.
