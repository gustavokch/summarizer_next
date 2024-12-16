// types/index.ts
export interface TranscriptionTask {
  task_id: string;
  video_url: string;
  video_title: string;
  transcription: string;
  summary: string;
}

export interface TranscribeResponse {
  task_id: string;
  video_url: string;
  video_title: string;
  transcription: string;
  summary: string;
}
