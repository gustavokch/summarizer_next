// components/TranscribeTab.tsx
import React, { useState } from 'react';
import { transcribeVideo } from '../services/api';
import { TranscribeResponse } from '../types';

interface TranscribeTabProps {
  onTranscriptionComplete: (task: TranscribeResponse) => void;
}

const TranscribeTab: React.FC<TranscribeTabProps> = ({ onTranscriptionComplete }) => {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const transcription = await transcribeVideo(youtubeUrl);
      onTranscriptionComplete(transcription);
      setYoutubeUrl('');
    } catch (err) {
      setError('Failed to transcribe video. Please try again.');
      console.error(err);
    } finally {
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
        {error && (
          <div className="text-red-500 bg-red-100 p-2 rounded-md">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600 disabled:bg-blue-300"
        >
          {isLoading ? 'Summarizing...' : 'Summarize'}
        </button>
      </form>

      {isLoading && (
        <div className="mt-4 text-center text-gray-500">
          Processing video... This may take a few moments.
        </div>
      )}
    </div>
  );
};

export default TranscribeTab;
