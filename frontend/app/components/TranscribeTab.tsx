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
    const message = activeTasksRef.current === 1
      ? 'Processing video... This may take a few moments.'
      : `Processing ${activeTasksRef.current} videos... This may take a few moments.`;

    if (!loadingToastIdRef.current) {
      loadingToastIdRef.current = toast.loading(message, {
        id: 'loading-toast'
      });
    } else {
      toast.loading(message, {
        id: 'loading-toast'
      });
    }
  };

  const processUrl = async (url: string): Promise<void> => {
    try {
      const transcription = await transcribeVideo(url.trim());
      onTranscriptionComplete(transcription);
      
      // Show individual success toast for each URL
      toast.success(`Transcription completed for: ${url.trim()}`);
    } catch (err) {
      // Show individual error toast for each failed URL
      toast.error(`Failed to transcribe: ${url.trim()}`, {
        description: err instanceof Error ? err.message : 'An unknown error occurred'
      });
      console.error(`Error processing ${url}:`, err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Split and filter URLs
    const urls = youtubeUrl
      .split(',')
      .map(url => url.trim())
      .filter(url => url.length > 0);

    if (urls.length === 0) {
      toast.error('Please enter at least one valid URL');
      return;
    }

    setIsLoading(true);
    activeTasksRef.current += urls.length;
    updateLoadingToast();

    try {
      // Process all URLs concurrently
      await Promise.allSettled(urls.map(url => 
        processUrl(url).finally(() => {
          activeTasksRef.current = Math.max(0, activeTasksRef.current - 1);
          if (activeTasksRef.current === 0) {
            toast.dismiss('loading-toast');
            loadingToastIdRef.current = null;
          } else {
            updateLoadingToast();
          }
        })
      ));

    } finally {
      setIsLoading(false);
      setYoutubeUrl('');
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="youtubeUrl" className="block mb-2 font-bold">
            Video URLs
          </label>
          <input
            type="text"
            id="youtubeUrl"
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            placeholder="https://youtube.com/watch?v=example1, https://youtube.com/watch?v=example2"
            required
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="mt-1 text-sm text-gray-500">
            Enter one or more URLs, separated by commas
          </p>
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