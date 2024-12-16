'use client'
/* eslint-disable */
import React, { useState, useEffect } from 'react';
import { fetchUserTasks, deleteTask } from '../services/api';
import { TranscriptionTask } from '../types';
import ReactMarkdown from 'react-markdown';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "../ui/collapsible";
import { Button } from "../ui/button";
import { ChevronDown, ChevronUp, Trash2 } from 'lucide-react';
import { toast } from "sonner"; // Assuming you're using a toast library

const HistoryTab: React.FC = () => {
  const [tasks, setTasks] = useState<TranscriptionTask[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTask, setSelectedTask] = useState<TranscriptionTask | null>(null)
  const [isTranscriptionOpen, setIsTranscriptionOpen] = useState(true)
  const [isSummaryOpen, setIsSummaryOpen] = useState(true)
  const [hoverTaskId, setHoverTaskId] = useState<string | null>(null)

  // Reload tasks function to be used after deletion
  const reloadTasks = async () => {
    try {
      const userTasks = await fetchUserTasks()
      setTasks(userTasks)
      
      // Reset selected task if current selection is deleted
      if (selectedTask && 
          !userTasks.some(task => task.task_id === selectedTask.task_id)) {
        setSelectedTask(null)
      }
    } catch (err) {
      toast.error('Failed to reload tasks');
    }
  }

  const handleDeleteTask = async (taskId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent task selection when deleting
    
    try {
      await deleteTask(taskId);
      toast.success('Task deleted successfully');
      await reloadTasks();
    } catch (error) {
      toast.error('Failed to delete task');
    }
  }

  useEffect(() => {
    const loadTasks = async () => {
      try {
        const userTasks = await fetchUserTasks()
        setTasks(userTasks)
        setIsLoading(false)
      } catch (err) {
        setError('Failed to load tasks')
        setIsLoading(false)
      }
    }

    loadTasks()
  }, [])

  const handleTaskSelect = (task: TranscriptionTask) => {
    setSelectedTask(task)
    setIsTranscriptionOpen(false)
    setIsSummaryOpen(true)
  }

  if (isLoading) {
    return <div className="p-6 text-center">Loading tasks...</div>
  }

  if (error) {
    return <div className="p-6 text-red-500">{error}</div>
  }

  return (
    <div className="w-full p-6 flex flex-col md:flex-row h-full">
      <div className="w-full md:w-1/4 pr-4 border-r mb-4 md:mb-0">
        <h2 className="font-bold mb-4">History</h2>
        {tasks.length === 0 ? (
          <p className="text-gray-500">No transcription tasks yet</p>
        ) : (
          <ul className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto">
            {tasks.map((task) => (
              <li 
                key={task.task_id}
                onMouseEnter={() => setHoverTaskId(task.task_id)}
                onMouseLeave={() => setHoverTaskId(null)}
                onClick={() => handleTaskSelect(task)}
                className={`
                  relative 

                  rounded-md 
                  cursor-pointer 
                  group 
                  ${selectedTask?.task_id === task.task_id 
                    ? 'bg-blue-100' 
                    : 'hover:bg-gray-100'
                  }
                `}
              >
                <div className="font-semibold flex items-center justify-between">
                  <span>{task.video_title}</span>
                  
                  {/* Delete Button */}
                  {hoverTaskId === task.task_id && (
                    <Button 
                      variant="destructive" 
                      size="sm" 
                      className="opacity-70 hover:opacity-100"
                      onClick={(e) => handleDeleteTask(task.task_id, e)}
                    >
                      <Trash2 size={16} />
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="w-full p-2 md:w-3/4 pl-4 flex-grow overflow-hidden">
      {selectedTask ? (
        <div className="h-full flex flex-col">
          <h3 className="text-xl font-bold mb-2 truncate">
            {selectedTask.video_title}
          </h3>
          <h4 className="text-small font-regular mb-2 truncate">
            URL:&nbsp; 
            <a
              href={selectedTask.video_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:underline"
            >
              {selectedTask.video_url}
            </a>
          </h4>
          <div className="overflow-y-auto space-y-4">


            <Collapsible open={isSummaryOpen} onOpenChange={setIsSummaryOpen}>
                <div className="flex items-center justify-between">
                  <h4 className="font-bold">Summary</h4>
                  <CollapsibleTrigger asChild>
                    <Button variant="ghost" size="sm">
                      {isSummaryOpen ? <ChevronUp /> : <ChevronDown />}
                    </Button>
                  </CollapsibleTrigger>
                </div>
                <CollapsibleContent>
                  <div className="p-2 rounded-md max-h-full overflow-y-scroll">
                    <ReactMarkdown>{selectedTask.summary}</ReactMarkdown>
                  </div>
                </CollapsibleContent>
              </Collapsible> 

              <Collapsible open={isTranscriptionOpen} onOpenChange={setIsTranscriptionOpen}>
                <div className="flex items-center justify-between">
                  <h4 className="font-bold">Transcription</h4>
                  <CollapsibleTrigger asChild>
                    <Button variant="ghost" size="sm">
                      {isTranscriptionOpen ? <ChevronUp /> : <ChevronDown />}
                    </Button>
                  </CollapsibleTrigger>
                </div>
                <CollapsibleContent>
                  <p className="p-2 rounded-md max-h-60 overflow-y-auto">
                    {selectedTask.transcription}
                  </p>
                </CollapsibleContent>
              </Collapsible>

            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-center">
            Select a task to view details
          </p>
        )}
      </div>
    </div>
  )
}

export default HistoryTab
/* eslint-enable */
