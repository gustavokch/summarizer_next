/* eslint-disable */
import React, { useState } from 'react';
import TranscribeTab from '../components/TranscribeTab';
import HistoryTab from '../components/HistoryTab';
import { TranscribeResponse } from '../types';

const Home: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'transcribe' | 'history'>('transcribe');
  const [latestTranscription, setLatestTranscription] = useState<TranscribeResponse | null>(null);

  const handleTranscriptionComplete = (task: TranscribeResponse) => {
    setLatestTranscription(task);
    setActiveTab('history');
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto bg-white rounded-lg shadow-lg">
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('transcribe')}
            className={`w-1/2 p-4 font-semibold ${
              activeTab === 'transcribe' 
                ? 'bg-blue-500 text-white' 
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Summarize Video
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`w-1/2 p-4 font-semibold ${
              activeTab === 'history' 
                ? 'bg-blue-500 text-white' 
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Task History
          </button>
        </div>

        {activeTab === 'transcribe' ? (
          <TranscribeTab onTranscriptionComplete={handleTranscriptionComplete} />
        ) : (
          <HistoryTab />
        )}
      </div>
    </div>
  );
};

export default Home;
/* eslint-enable */