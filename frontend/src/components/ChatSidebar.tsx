'use client';

import Link from 'next/link';
import { IoCloseSharp, IoTrashOutline } from 'react-icons/io5';
import { useAuth } from '@/context/AuthProvider';
import { useState } from 'react';


interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  isDarkMode: boolean;
}

export default function ChatSidebar({ isOpen, onClose, isDarkMode }: ChatSidebarProps) {
  const { user } = useAuth();
  const userId = user?.id;

  // TODO: Get sessions from user
  // TODO: Add session creation
  const [sessions, setSessions] = useState([
    { id: 'Info01' },
    { id: 'Change me!' }
  ]);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const handleDelete = () => {
    if (deleteId) {
      setSessions(sessions => sessions.filter(s => s.id !== deleteId));
      setDeleteId(null);
    }
  };

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
          <h3 className={`font-semibold ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>Information</h3>
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
                {session.id}
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">
          <div className={`rounded-xl shadow-xl p-6 w-[90%] max-w-xs ${
            isDarkMode ? 'bg-gray-800' : 'bg-white'
          }`}>
            <div className={`text-lg font-semibold mb-3 ${
              isDarkMode ? 'text-gray-200' : 'text-gray-800'
            }`}>
              Are you sure you want to delete this conversation?
            </div>
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => setDeleteId(null)}
                className={`px-4 py-1 rounded transition-colors duration-200 ${
                  isDarkMode 
                    ? 'bg-gray-700 hover:bg-gray-600 text-gray-200' 
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-1 rounded bg-red-500 hover:bg-red-600 text-white transition-colors duration-200"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-30 sm:hidden"
          onClick={onClose}
        />
      )}
    </>
  );
}