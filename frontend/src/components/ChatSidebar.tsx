'use client';

import Link from 'next/link';
import { useAuth } from '@/context/AuthProvider';
import { useRouter } from 'next/navigation';
import { useState, useEffect, useCallback } from 'react';
import { IoCloseSharp, IoTrashOutline, IoPencil, IoCheckmark, IoClose } from 'react-icons/io5';
import { deleteChatSession, getChatSessions, updateChatTitle } from '@/services/api';
import { ChatListItem } from '@/types/chat';


interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  isDarkMode: boolean;
  currentChatId: string;
}

export default function ChatSidebar({ isOpen, onClose, isDarkMode, currentChatId }: ChatSidebarProps) {
  const { user } = useAuth();
  const router = useRouter();
  const [sessions, setSessions] = useState<ChatListItem[]>([]);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [newSession, setNewSession] = useState<ChatListItem | null>(null);

  const fetchSessions = useCallback(async () => {
    if (!user) return;
    try {
      const fetchedSessions = await getChatSessions();
      const activeSessions = fetchedSessions.filter(session => session.message_count > 0).map(session => ({
        session_id: session.session_id,
        title: session.title,
        created_at: session.created_at,
        last_active: session.last_active || session.created_at,
        message_count: session.message_count
      }));
      setSessions(activeSessions);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
  }, [user]);

  useEffect(() => {
    if (currentChatId && currentChatId !== 'new') {
      const isNewSession = !sessions.some(session => session.session_id === currentChatId);
      if (isNewSession) {
        const newSessionItem: ChatListItem = {
          session_id: currentChatId,
          title: 'New Chat',
          created_at: new Date().toISOString(),
          last_active: new Date().toISOString(),
          message_count: 1
        };
        setNewSession(newSessionItem);
        setSessions(prev => {
          if (prev.some(session => session.session_id === currentChatId)) {
            return prev;
          }
          return [newSessionItem, ...prev];
        });
      }
    }
  }, [currentChatId, sessions]);

  // TODO: remove this, use another way to fetch sessions
  useEffect(() => {
    if (newSession) {
      const timer = setTimeout(() => {
        setNewSession(null);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [newSession]);

  useEffect(() => {
    if (user && isOpen) {
      fetchSessions();
      const interval = setInterval(fetchSessions, 5000);
      return () => clearInterval(interval);
    }
  }, [user, fetchSessions, isOpen]);

  const handleCreateSession = async () => {
    if (!user) return;
    setIsCreating(true);
    try {
      router.push(`/chat/${user?.id}/new`);
      onClose();
    } catch (error) {
      console.error('Failed to create session:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteId) return;
    try {
      await deleteChatSession(deleteId);
      setSessions(prevSessions => prevSessions.filter(s => s.session_id !== deleteId));

      if (currentChatId === deleteId) {
        handleCreateSession();
      }
      setDeleteId(null);
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const handleEditClick = (session: ChatListItem) => {
    setEditingId(session.session_id);
    setEditingTitle(session.title || '');
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditingTitle('');
  };

  const handleSaveTitle = async () => {
    if (!editingId || !editingTitle.trim() || isSaving) return;

    setIsSaving(true);
    try {
      await updateChatTitle(editingId, editingTitle.trim());

      setSessions(prev =>
        prev.map(s => s.session_id === editingId ? { ...s, title: editingTitle.trim() } : s)
      );

      handleCancelEdit();
    } catch (error) {
      console.error('Failed to save title:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 sm:hidden"
          onClick={onClose}
        ></div>
      )}
      <aside
        className={`
          fixed top-0 left-0 h-full w-72 md:w-56 shadow-lg z-40 
          transition-transform duration-300 ease-in-out
          ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          sm:translate-x-0
        `}
      >
        <div className={`h-14 pl-4 pr-2 border-b flex justify-between items-center ${isDarkMode ? 'border-gray-700' : 'border-gray-200'
          }`}>
          <h3 className={`font-semibold ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>Chat History</h3>
          <button
            className={`sm:hidden p-2 rounded-full transition-colors duration-200 cursor-pointer ${isDarkMode
              ? 'text-gray-400 hover:bg-gray-700'
              : 'text-gray-600 hover:bg-gray-200'
              }`}
            onClick={onClose}
            title="Close sidebar"
          >
            <IoCloseSharp size={24} />
          </button>
        </div>

        <div className="p-2">
          <button
            onClick={handleCreateSession}
            className={`w-full p-2 mb-2 rounded-md font-semibold transition-colors duration-200 flex items-center justify-center cursor-pointer ${isDarkMode
              ? 'bg-[#0F396D] hover:bg-[#0056b3] text-white'
              : 'bg-[#0056b3] hover:bg-[#0F396D] text-white'
              } ${isCreating ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isCreating ? 'Creating...' : '+ New Chat'}
          </button>

          <div className="flex flex-col space-y-1 overflow-y-auto max-h-[calc(100vh-8rem)]">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className={`flex items-center group rounded-md p-2 transition-all duration-300 ease-in-out
                  ${currentChatId === session.session_id
                    ? (isDarkMode ? 'bg-gray-700' : 'bg-gray-200')
                    : (isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200')
                  }
                  ${newSession?.session_id === session.session_id ? 'animate-fade-in' : ''}
                `}
              >
                {user && editingId === session.session_id ? (
                  <>
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      className={`flex-1 bg-transparent border-b text-sm outline-none ${isDarkMode ? 'border-gray-500 text-white' : 'border-gray-400 text-black'}`}
                      autoFocus
                      onKeyDown={(e) => { if (e.key === 'Enter') handleSaveTitle(); if (e.key === 'Escape') handleCancelEdit(); }}
                      title="Edit title"
                      placeholder="Enter new title"
                    />
                    <button onClick={handleSaveTitle} disabled={isSaving} className="p-1 ml-2 cursor-pointer text-green-500 hover:bg-gray-600 rounded-full" title="Save title">
                      <IoCheckmark size={18} />
                    </button>
                    <button onClick={handleCancelEdit} className="p-1 cursor-pointer text-gray-400 hover:bg-gray-600 rounded-full" title="Cancel editing">
                      <IoClose size={18} />
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      href={`/chat/${user?.id}/${session.session_id}`}
                      className={`flex-1 block text-sm truncate ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}
                      onClick={onClose}
                    >
                      {session.title || 'New Chat'}
                    </Link>
                    <div className="flex items-center md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                      <button className="p-1 cursor-pointer" title="Edit title" onClick={() => handleEditClick(session)}>
                        <IoPencil className={`${isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-800'}`} size={16} />
                      </button>
                      <button className="p-1 cursor-pointer" title="Delete chat" onClick={() => setDeleteId(session.session_id)}>
                        <IoTrashOutline className={`${isDarkMode ? 'text-gray-400 hover:text-red-500' : 'text-gray-600 hover:text-red-500'}`} size={16} />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </aside>

      {deleteId && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 transition-opacity duration-300 animate-fade-in"
          onClick={() => setDeleteId(null)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className={`
            relative w-full max-w-md rounded-2xl shadow-xl animate-pop-in
            ${isDarkMode ? 'bg-gray-800 border border-gray-700' : 'bg-white'}
          `}
          >
            <div className="flex flex-col items-center p-6 sm:p-8 text-center">
              <div className={`flex items-center justify-center size-12 rounded-full mb-4 ${isDarkMode ? 'bg-red-900/50' : 'bg-red-100'}`}>
                <IoTrashOutline className={`size-6 ${isDarkMode ? 'text-red-400' : 'text-red-600'}`} />
              </div>
              <h3 className={`text-xl font-semibold mb-2 ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                Delete Chat?
              </h3>
              <p className={`text-sm mb-6 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Are you sure you want to delete this chat session? <br /> This action cannot be undone.
              </p>
              <div className="grid grid-cols-2 gap-4 w-full">
                <button
                  onClick={() => setDeleteId(null)}
                  className={`
                  w-full px-4 py-2.5 rounded-lg font-semibold text-sm transition-colors duration-200 cursor-pointer
                  ${isDarkMode
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                      : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
                    }
                `}
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteConfirm}
                  className="w-full px-4 py-2.5 rounded-lg font-semibold text-sm text-white bg-red-900 hover:bg-red-800 transition-colors duration-200 cursor-pointer"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}