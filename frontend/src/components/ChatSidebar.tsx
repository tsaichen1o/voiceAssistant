'use client';

import Link from 'next/link';
import { IoCloseSharp } from 'react-icons/io5';
import { useAuth } from '@/context/AuthProvider';


interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ChatSidebar({ isOpen, onClose }: ChatSidebarProps) {
  const { user } = useAuth();
  const userId = user?.id;

  // TODO: Get sessions from user
  // TODO: Add session creation
  const sessions = [{ id: 'Info01' }, { id: 'I think this place can change to another thing.' }];

  return (
    <>
      <aside
        className={`fixed top-0 left-0 h-screen w-56 bg-gray-50 shadow z-40 transform ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } sm:translate-x-0 transition-transform duration-300 ease-in-out`}
      >
        <div className="h-14 px-4 border-b flex justify-between items-center border-gray-200">
          <h3 className="font-semibold text-gray-800">Information</h3>
          <button
            className="sm:hidden p-2 text-gray-800 hover:bg-gray-200 rounded-full"
            onClick={onClose}
            title="Close sidebar"
          >
            <IoCloseSharp size={20} />
          </button>
        </div>
        <nav className="p-2 text-gray-800">
          {sessions.map((session) => (
            <Link
              key={session.id}
              href={`/chat/${userId}/${session.id}`}
              className="block p-2 hover:bg-gray-200 rounded-md"
              onClick={onClose}
            >
              {session.id}
            </Link>
          ))}
        </nav>
      </aside>

      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-30 sm:hidden"
          onClick={onClose}
        />
      )}
    </>
  );
}