/**
 * Message model
 */
export interface ChatMessage {
  id: string;
  session_id: string;
  chat_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  isStreaming?: boolean;
  streamUrl?: string;
}

/**
 * Session model
 */
export interface ChatSessionInfo {
  id: string;
  user_id: string;
  session_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  last_active: string;
  message_count: number;
}

/**
 * For Chat Sidebar
 * GET /api/sessions
 */
export interface ChatListItem {
  session_id: string;
  title: string | null;
  created_at: string;
  last_active: string;
  message_count: number;
}

/**
 * For Chat History
 * GET /api/sessions/{id}
 */
export interface ChatHistoryResponse {
  session_id: string;
  title: string | null;
  messages: ChatMessage[];
  created_at: string;
  last_active: string;
}