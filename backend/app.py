import asyncio
import aiofiles
import functools
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
origins = [
    "http://localhost:3000",  # Add your Next.js app's URL
    "http://100.99.252.20:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Origins that are allowed to access your backend
    allow_credentials=True,  # Allow cookies to be sent
    allow_methods=["*"],  # HTTP methods allowed
    allow_headers=["*"],  # HTTP headers allowed
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

async def extract_audio(url: str) -> tuple[str, str]:
    """Asynchronously extract audio from YouTube video."""
    ydl_opts = {
        'proxy': 'socks5://dante_user:uygbnjH0112@100.115.246.43:1080',
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
        }],
        'outtmpl': os.path.join(UPLOAD_DIRECTORY, '%(title)s.%(ext)s')
    }
    
    # Use run_in_executor to make yt-dlp operations async
    loop = asyncio.get_running_loop()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
        audio_file = await loop.run_in_executor(None, lambda: ydl.prepare_filename(info_dict))
        audio_file = audio_file.rsplit(".", 1)[0] + ".opus"
        video_title = info_dict.get('title', None)
    
    return audio_file, video_title

async def get_file_size(file_path):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, os.path.getsize, file_path)

async def transcribe_audio(audio_path: str) -> str:
    """Asynchronously transcribe audio using Gemini."""
    if not genai:
        return "Transcription service is currently unavailable."
    
    try:
        file_size = await get_file_size(file_path=audio_path)
        if file_size > 20971520:
        # Use aiofiles for async file size check and reading
            async with aiofiles.open(audio_path, 'rb') as file:
                await file.seek(0)
                model = genai.GenerativeModel(model_name)
                # Async file upload
                genai_file = await asyncio.to_thread(genai.upload_file, path=audio_path)
                print("Transcribing audio...")
                response = await asyncio.to_thread(
                    model.generate_content,
                    [system_prompt, genai_file],
                    generation_config=genai.GenerationConfig(temperature=0.1)
                )
            return response.text

        else:
            async with aiofiles.open(audio_path, 'rb') as file:
                model = genai.GenerativeModel(model_name)
                file_data = await file.read()
                print("Transcribing audio...")
                response = await asyncio.to_thread(
                    model.generate_content,
                        [system_prompt, {
                            "mime_type": "audio/mp3",
                            "data": file_data
                        }],
                        generation_config=genai.GenerationConfig(temperature=0.1)
                    )
                return response.text

    except Exception as e:
        print(f"Transcription error: {e}")
        return f"Transcription failed: {str(e)}"

async def summarize_text(text: str) -> str:
    """Asynchronously summarize transcribed text using Gemini."""
    if not genai:
        return "Summary service is currently unavailable."
    
    try:
        print("Summarizing text...")
        model = genai.GenerativeModel(model_name, system_instruction=summarize_prompt)
        response = await asyncio.to_thread(
            model.generate_content,
            f"{text}",
            generation_config=genai.GenerationConfig(max_output_tokens=8191, temperature=0.3)
        )
        return response.text
    
    except Exception as e:
        print(f"Summarization error: {e}")
        return f"Summarization failed: {str(e)}"

async def process_youtube_video(url: str) -> dict:
    """
    Async workflow to extract audio, transcribe, and summarize.
    
    Returns a dictionary with processing results.
    """
    try:
        # Extract audio
        audio_file, video_title = await extract_audio(url)
        
        # Transcribe audio
        transcription = await transcribe_audio(audio_file)
        
        # Summarize transcription
        summary = await summarize_text(transcription)
        
        return {
            'video_title': video_title,
            'audio_file': audio_file,
            'transcription': transcription,
            'summary': summary
        }
    
    except Exception as e:
        return {
            'error': str(e)
        }


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

#        video_title, audio_file, transcription, summary = await process_youtube_video(transcription_request.youtube_url)
        result = await process_youtube_video(transcription_request.youtube_url)
        # Store task in database
        task = TranscriptionTask(
            session_id=session_id,
            video_url=transcription_request.youtube_url,
            video_title=result.get('video_title'),
            audio_path=result.get('audio_file'),
            transcription=result.get('transcription'),
            summary=result.get('summary')
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Return response
        return TranscriptionResponse(
            task_id=str(task.id),
            video_url=transcription_request.youtube_url,
            video_title=result.get('video_title'),
            transcription=result.get('transcription'),
            summary=result.get('summary')
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
