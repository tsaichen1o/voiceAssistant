export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  isStreaming?: boolean;
  streamUrl?: string;
}

export interface ChatSession {
  id: string;
  messages: ChatMessage[];
} 