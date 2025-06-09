'use client';

import Link from 'next/link';
import { IoCloseSharp, IoTrashOutline } from 'react-icons/io5';
import { useAuth } from '@/context/AuthProvider';
import { useState, useEffect, useCallback } from 'react';
import { createChatSession, deleteChatSession, getChatSessions } from '@/services/api';

// TODO: get all sessions from the backend

interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  isDarkMode: boolean;
}

interface Session {
  id: string;
  title?: string;
}

interface SessionHistoryResponse {
  session_id: string;
  title?: string;
  created_at: string;
  last_active: string;
  message_count: number;
  user_id: string;
}

export default function ChatSidebar({ isOpen, onClose, isDarkMode }: ChatSidebarProps) {
  const { user } = useAuth();
  const userId = user?.id;
  const [sessions, setSessions] = useState<Session[]>([]);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchSessions = useCallback(async () => {
    if (!userId) return;
    try {
      const response = await getChatSessions();
      const formattedSessions = response.map((session: SessionHistoryResponse) => ({
        id: session.session_id,
        title: session.title || 'New Chat'
      }));
      setSessions(formattedSessions);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
  }, [userId]);

  const handleCreateSession = async () => {
    if (!userId) return;
    setIsLoading(true);
    try {
      const response = await createChatSession();
      if (response.session_id) {
        await fetchSessions();
      }
    } catch (error) {
      console.error('Failed to create session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await deleteChatSession(deleteId);
      setSessions(sessions => sessions.filter(s => s.id !== deleteId));
      setDeleteId(null);
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  useEffect(() => {
    if (userId) {
      fetchSessions();
    }
  }, [userId, fetchSessions]);

  return (
    <>
      <aside
        className={`fixed top-0 left-0 h-screen w-72 md:w-56 shadow z-40 transform ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } sm:translate-x-0 transition-transform duration-300 ease-in-out ${
          isDarkMode ? 'bg-gray-800' : 'bg-gray-50'
        }`}
      >
        <div className={`h-14 pl-4 pr-2 border-b flex justify-between items-center ${
          isDarkMode ? 'border-gray-700' : 'border-gray-200'
        }`}>
          <h3 className={`font-semibold ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>Chat Sessions</h3>
          <button
            className={`sm:hidden pr-1 rounded-full transition-colors duration-200 ${
              isDarkMode 
                ? 'text-gray-200 hover:bg-gray-700' 
                : 'text-gray-800 hover:bg-gray-200'
            }`}
            onClick={onClose}
            title="Close sidebar"
          >
            <IoCloseSharp size={20} />
          </button>
        </div>
        <div className={`p-2 space-y-1 ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>
          <button
            onClick={handleCreateSession}
            disabled={isLoading}
            className={`w-full p-2 rounded-md transition-colors duration-200 ${
              isDarkMode 
                ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                : 'bg-blue-500 hover:bg-blue-600 text-white'
            } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isLoading ? 'Creating...' : 'New Chat'}
          </button>
          {sessions.map((session) => (
            <div key={session.id} className="flex items-center group">
              <Link
                href={`/chat/${userId}/${session.id}`}
                className={`flex-1 block p-2 rounded-md transition-colors duration-200 ${
                  isDarkMode 
                    ? 'hover:bg-gray-700' 
                    : 'hover:bg-gray-200'
                }`}
                onClick={onClose}
              >
                {session.title}
              </Link>
              <button
                className={`ml-2 p-1 opacity-60 hover:opacity-100 rounded-full transition-colors duration-200 ${
                  isDarkMode 
                    ? 'hover:bg-gray-700' 
                    : 'hover:bg-blue-50'
                } cursor-pointer`}
                title="Delete"
                onClick={() => setDeleteId(session.id)}
              >
                <IoTrashOutline className={isDarkMode ? 'text-blue-400' : 'text-blue-500'} size={18} />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {deleteId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
            <p className={`mb-4 ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>
              Are you sure you want to delete this chat?
            </p>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setDeleteId(null)}
                className={`px-4 py-2 rounded-md ${
                  isDarkMode 
                    ? 'bg-gray-700 hover:bg-gray-600 text-gray-200' 
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 rounded-md bg-red-600 hover:bg-red-700 text-white"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}