'use client';

import Link from 'next/link';
import { IoCloseSharp, IoTrashOutline } from 'react-icons/io5';
import { useAuth } from '@/context/AuthProvider';
import { useState } from 'react';


interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ChatSidebar({ isOpen, onClose }: ChatSidebarProps) {
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
        className={`fixed top-0 left-0 h-screen w-72 md:w-56 bg-gray-50 shadow z-40 transform ${isOpen ? 'translate-x-0' : '-translate-x-full'
          } sm:translate-x-0 transition-transform duration-300 ease-in-out`}
      >
        <div className="h-14 pl-4 pr-2 border-b flex justify-between items-center border-gray-200">
          <h3 className="font-semibold text-gray-800">Information</h3>
          <button
            className="sm:hidden pr-1 text-gray-800 hover:bg-gray-200 rounded-full"
            onClick={onClose}
            title="Close sidebar"
          >
            <IoCloseSharp size={20} />
          </button>
        </div>
        <div className="p-2 text-gray-800 space-y-1">
          {sessions.map((session) => (
            <div key={session.id} className="flex items-center group">
              <Link
                href={`/chat/${userId}/${session.id}`}
                className="flex-1 block p-2 hover:bg-gray-200 rounded-md transition"
                onClick={onClose}
              >
                {session.id}
              </Link>
              <button
                className="ml-2 p-1 opacity-60 hover:opacity-100 hover:bg-blue-50 rounded-full transition cursor-pointer"
                title="Delete"
                onClick={() => setDeleteId(session.id)}
              >
                <IoTrashOutline className="text-blue-500" size={18} />
              </button>
            </div>
          ))}
        </div>
      </aside>
      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20">
          <div className="bg-white rounded-xl shadow-xl p-6 w-[90%] max-w-xs">
            <div className="text-lg font-semibold mb-3 text-gray-800">
              Are you sure you want to delete this conversation?
            </div>
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => setDeleteId(null)}
                className="px-4 py-1 rounded bg-gray-200 hover:bg-gray-300 text-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-1 rounded bg-red-500 hover:bg-red-600 text-white"
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