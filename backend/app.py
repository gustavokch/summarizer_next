import asyncio
import os
import pathlib
import uuid
from datetime import datetime, timedelta
from templates import system_prompt, summarize_prompt
import yt_dlp
import uvicorn

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel as PydanticBaseModel, Field
from pydantic.config import ConfigDict
from dotenv import load_dotenv
class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True)
from sqlalchemy import (Column, DateTime, Integer, String, Text, 
                        create_engine, ForeignKey)
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

# Updated Gemini import with error handling
try:
    import google.generativeai as genai
except ImportError:
    print("Google Generative AI library not found. Please install google-generativeai.")
    genai = None

# Configuration and Environment Variables
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./transcription_db.sqlite')
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY', 'Not set')
UPLOAD_DIRECTORY = os.getenv('UPLOAD_DIRECTORY', './uploads')
if os.getenv('GOOGLE_API_KEY') == 'Not set':
    with open(f"api_key", "r") as f:
        GEMINI_API_KEY = str(f.readline())
        print("Key read from api_key: "+str(f.readline()))
        os.environ['GOOGLE_API_KEY'] = str(f.readline())
        
print("API Key: "+str(os.getenv('GOOGLE_API_KEY')))
# Ensure upload directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Database Setup
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
model_name = 'models/gemini-1.5-flash'

# Configure Gemini API
if genai and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        genai = None

# Database Models
class UserSession(Base):
    __tablename__ = 'user_sessions'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TranscriptionTask(Base):
    __tablename__ = 'transcription_tasks'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey('user_sessions.session_id'))
    video_url = Column(String, index=True)
    video_title = Column(String)
    audio_path = Column(String)
    transcription = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create database tables
Base.metadata.create_all(bind=engine)

# Pydantic models for request/response
class TranscriptionRequest(BaseModel):
    youtube_url: str = Field(..., description="YouTube video URL")

class TranscriptionResponse(BaseModel):
    task_id: str
    video_url: str
    video_title: str
    transcription: str
    summary: str

# FastAPI App Setup
app = FastAPI(title="Video Transcription Service")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_or_get_session(request: Request, response: Response, db: Session) -> str:
    """Create or retrieve a consistent user session."""
    session_cookie = request.cookies.get('session_id')
    
    if not session_cookie:
        # Generate a new session ID if no existing cookie
        session_cookie = str(uuid.uuid4())
        
        # Ensure the session is stored in the database
        existing_session = db.query(UserSession).filter(
            UserSession.session_id == session_cookie
        ).first()
        
        if not existing_session:
            new_session = UserSession(session_id=session_cookie)
            db.add(new_session)
            db.commit()
        
        # Set the session cookie with a 1-month expiration
        response.set_cookie(
            key="session_id", 
            value=session_cookie, 
            httponly=True, 
            max_age=30 * 24 * 3600,  # 30 days
            secure=True,
            samesite='lax'
        )
    
    return session_cookie

def extract_audio(url: str) -> str:
    """Extract audio from YouTube video."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
        }],
        'outtmpl': os.path.join(UPLOAD_DIRECTORY, '%(title)s.%(ext)s')
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        audio_file = ydl.prepare_filename(info_dict)
        audio_file = audio_file.rsplit(".", 1)[0] + ".opus"
        video_title = info_dict.get('title', None)
    
    return audio_file, video_title

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using Gemini."""
    if not genai:
        return "Transcription service is currently unavailable."
    
    try:
        file_size = os.path.getsize(f"{audio_path}")
        if file_size > 20971520:
            model = genai.GenerativeModel(model_name)
            genai_file = genai.upload_file(path=f"{audio_path}")
            response = model.generate_content(
                    [system_prompt, genai_file],
                    generation_config = genai.GenerationConfig(temperature=0.1)
            )     
            return response.text

        else: 
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                    [system_prompt,
                    {
                        "mime_type": "audio/mp3",
                        "data": pathlib.Path(f"{audio_path}").read_bytes()
                    }
                    ],
                    generation_config = genai.GenerationConfig(temperature=0.1)
            )     
            return response.text

    except Exception as e:
        print(f"Transcription error: {e}")
        return f"Transcription failed: {str(e)}"

def summarize_text(text: str) -> str:
    """Summarize transcribed text using Gemini."""
    if not genai:
        return "Summary service is currently unavailable."
    
    try:
        model = genai.GenerativeModel(model_name,system_instruction=summarize_prompt)
        response = model.generate_content(
            f"{text}",
            generation_config = genai.GenerationConfig(max_output_tokens=8191, temperature=0.3)
        )
        return response.text
    
    except Exception as e:
        print(f"Summarization error: {e}")
        return f"Summarization failed: {str(e)}"
    
@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_youtube_video(
    request: Request, 
    response: Response,
    transcription_request: TranscriptionRequest,
    db: Session = Depends(get_db)
):
    """
    Transcribe and summarize a YouTube video
    - Check if video has been processed before
    - If not, extract audio, transcribe, and summarize
    - Store results
    """
    try:
        # Get consistent session ID
        session_id = create_or_get_session(request, response, db)
        
        # Check if this video URL has already been processed for this session
        existing_task = db.query(TranscriptionTask).filter(
            and_(
                TranscriptionTask.session_id == session_id,
                TranscriptionTask.video_url == transcription_request.youtube_url
            )
        ).first()
        
        # If task exists, return existing results
        if existing_task:
            return TranscriptionResponse(
                task_id=str(existing_task.id),
                video_url=existing_task.video_url,
                video_title=existing_task.video_title,
                transcription=existing_task.transcription,
                summary=existing_task.summary
            )
        
        # Run extract_audio and extract_title in parallel
        audio_path, video_title = extract_audio(transcription_request.youtube_url)
#            extract_title_async(transcription_request.youtube_url)
#        )
        
        # Transcribe
        print("Transcribing audio...")
        transcription = transcribe_audio(audio_path)
        print("Audio transcribed!")
        
        # Summarize
        print("Summarizing text...")
        summary = summarize_text(transcription)
        print("Text summarized!")
        
        # Store task in database
        task = TranscriptionTask(
            session_id=session_id,
            video_url=transcription_request.youtube_url,
            video_title=video_title,
            audio_path=audio_path,
            transcription=transcription,
            summary=summary
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Return response
        return TranscriptionResponse(
            task_id=str(task.id),
            video_url=transcription_request.youtube_url,
            video_title=video_title,
            transcription=transcription,
            summary=summary
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks", response_model=list[TranscriptionResponse])
async def get_user_tasks(
    request: Request, 
    response: Response,
    db: Session = Depends(get_db)
):
    """Retrieve all tasks for the current user session."""
    session_id = create_or_get_session(request, response, db)
    
    tasks = db.query(TranscriptionTask).filter(
        TranscriptionTask.session_id == session_id
    ).all()
    
    return [
        TranscriptionResponse(
            task_id=str(task.id),
            video_url=task.video_url,
            video_title=task.video_title,
            transcription=task.transcription,
            summary=task.summary
        ) for task in tasks
    ]

@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    request: Request, 
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Delete a specific task for the current user session.
    
    Args:
        task_id (int): The ID of the task to delete
        request (Request): The incoming HTTP request
        response (Response): The HTTP response to potentially modify
        db (Session): Database session dependency
    
    Returns:
        dict: A confirmation message about the deletion
    """
    try:
        # Get the current session ID
        session_id = create_or_get_session(request, response, db)
        
        # Find the task, ensuring it belongs to the current session
        task = db.query(TranscriptionTask).filter(
            and_(
                TranscriptionTask.id == task_id,
                TranscriptionTask.session_id == session_id
            )
        ).first()
        
        # If task not found, raise a 404 error
        if not task:
            raise HTTPException(
                status_code=404, 
                detail="Task not found or not authorized for deletion"
            )
        
        # Optional: Remove the audio file if you want to clean up storage
        try:
            if task.audio_path and os.path.exists(task.audio_path):
                os.remove(task.audio_path)
        except Exception as file_error:
            # Log the file deletion error but don't prevent task deletion
            print(f"Could not delete audio file: {file_error}")
        
        # Delete the task from the database
        db.delete(task)
        db.commit()
        
        return {"message": "Task deleted successfully"}
    
    except SQLAlchemyError as db_error:
        # Handle database-related errors
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Database error during task deletion: {str(db_error)}"
        )
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error during task deletion: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)