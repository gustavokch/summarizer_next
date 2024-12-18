import React, { useState, useRef } from 'react';
import { toast } from 'sonner';
import { transcribeVideo } from '../services/api';
import { TranscribeResponse } from '../types';

interface TranscribeTabProps {
  onTranscriptionComplete: (task: TranscribeResponse) => void;
}

const TranscribeTab: React.FC<TranscribeTabProps> = ({ onTranscriptionComplete }) => {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const activeTasksRef = useRef(0);
  const loadingToastIdRef = useRef<string | number | null>(null);

  const updateLoadingToast = () => {
    if (activeTasksRef.current > 0) {
      const message = activeTasksRef.current === 1
        ? 'Processing video... This may take a few moments.'
        : `Processing ${activeTasksRef.current} videos... This may take a few moments.`;
      
      if (loadingToastIdRef.current) {
        toast.dismiss(loadingToastIdRef.current);
      }
      loadingToastIdRef.current = toast.loading(message);
    } else {
      if (loadingToastIdRef.current) {
        toast.dismiss(loadingToastIdRef.current);
        loadingToastIdRef.current = null;
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // Increment active tasks counter and update toast
      activeTasksRef.current += 1;
      updateLoadingToast();

      const transcription = await transcribeVideo(youtubeUrl);
      
      // Show success toast
      toast.success('Video transcription completed successfully');
      
      onTranscriptionComplete(transcription);
      setYoutubeUrl('');
    } catch (err) {
      // Show error toast
      toast.error('Failed to transcribe video. Please try again.', {
        description: err instanceof Error ? err.message : 'An unknown error occurred'
      });
      console.error(err);
    } finally {
      // Decrement active tasks counter and update toast
      activeTasksRef.current = Math.max(0, activeTasksRef.current - 1);
      updateLoadingToast();
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="youtubeUrl" className="block mb-2 font-bold">
            Video URL
          </label>
          <input
            type="url"
            id="youtubeUrl"
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            placeholder="https://youtube.com/watch?v=example"
            required
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          className="w-full bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600 disabled:bg-blue-300"
        >
          Summarize
        </button>
      </form>
    </div>
  );
};

export default TranscribeTab;