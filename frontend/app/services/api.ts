// services/api.ts
import axios from 'axios';
import { TranscriptionTask, TranscribeResponse } from '../types';
//const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api';
//const API_BASE_URL = '/api';  // Now points to Next.js API route
const API_BASE_URL = 'http://localhost:8090'; // Adjust to your FastAPI backend URL

export const transcribeVideo = async (youtubeUrl: string): Promise<TranscribeResponse> => {
  try {
    const response = await axios.post<TranscribeResponse>(`${API_BASE_URL}/transcribe`, {
      youtube_url: youtubeUrl
    }, {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Transcription error:', error);
    throw error;
  }
};

export const fetchUserTasks = async (): Promise<TranscriptionTask[]> => {
  try {
    const response = await axios.get<TranscriptionTask[]>(`${API_BASE_URL}/tasks`, {
      withCredentials: true
    });
    return response.data;
  } catch (error) {
    console.error('Fetch tasks error:', error);
    throw error;
  }
};

export const deleteTask = async (taskId: string) => {
  try {
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
      method: 'DELETE',
      credentials: 'include', // Important for maintaining session
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to delete task');
    }

    return await response.json();
  } catch (error) {
    console.error('Task deletion error:', error);
    throw error;
  }
};