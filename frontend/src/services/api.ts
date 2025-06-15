import { supabase } from '@/libs/supabase';
import { ChatMessage, ChatSessionInfo, ChatListItem } from '@/types/chat';


const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface StreamInitiationResponse {
  stream_id: string;
  session_id: string;
}

export interface ChatSessionResponse {
  session_id: string;
  created: boolean;
}

export interface ChatSessionHistoryResponse {
  session_id: string;
  title: string | null;
  messages: ChatMessage[];
  created_at: string;
  last_active: string;
}
// ------------------ Auth API ------------------
export async function getAccessToken() {
  // The session here is the session of the user who is logged in
  const { data, error } = await supabase.auth.getSession();
  if (error || !data.session) throw new Error('User not authenticated');
  return data.session.access_token;
}

export async function getCurrentUser() {
  const { data, error } = await supabase.auth.getSession();
  if (error || !data.session) throw new Error('User not authenticated');
  return data.session.user;
}


// ------------------ Chat Session API ------------------
export async function getChatSessions(): Promise<ChatSessionInfo[]> {
  const token = await getAccessToken();
  const res = await fetch(`${API_URL}/api/sessions`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error('Failed to get chat sessions');
  return res.json();
}

export async function createChatSession(): Promise<ChatSessionResponse> {
  const token = await getAccessToken();
  const res = await fetch(`${API_URL}/api/sessions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  if (!res.ok) throw new Error('Failed to create chat session');
  return res.json();
}


export async function getChatSessionHistory(chatSessionId: string): Promise<ChatSessionHistoryResponse> {
  const token = await getAccessToken();
  const res = await fetch(`${API_URL}/api/sessions/${chatSessionId}`, {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to get chat session');
  return res.json();
}


// TODO: error handling
export async function deleteChatSession(chatSessionId: string) {
  const token = await getAccessToken();
  const res = await fetch(`${API_URL}/api/sessions/${chatSessionId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error('Failed to delete chat session');
  return res.json();
}


// ------------------ Chat Message API ------------------
/**
 * Send a message to the backend to initiate a chat response.
 * Based on the stream parameter, the backend will decide whether to return a complete answer or start a stream.
 * We always request streaming output.
 * @param messages Chat history messages
 * @param chatSessionId Current session ID
 * @returns An object containing stream_id, used to establish an EventSource connection later
 */
export async function sendMessage(
  messages: ChatMessage[],
  chatSessionId?: string
): Promise<StreamInitiationResponse> {
  const token = await getAccessToken();

  const res = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages: messages.map(m => ({
        role: m.role,
        content: m.content,
        created_at: m.created_at,
      })),
      session_id: chatSessionId,
      temperature: 0.7,
      max_tokens: 1000,
      stream: true,
    }),
  });

  if (!res.ok) {
    const errText = await res.text();
    console.error('API ERROR:', res.status, errText);
    throw new Error('Failed to initiate chat stream');
  }
  
  return res.json();
}

export async function saveChatHistory(messages: ChatMessage[], sessionId: string) {
  const token = await getAccessToken();

  const res = await fetch(`${API_URL}/api/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ messages }),
  });

  if (!res.ok) {
    const errText = await res.text();
    console.error("API Error on save:", errText);
    throw new Error('Failed to save chat history');
  }

  return res.json();
}


export async function updateChatTitle(sessionId: string, title: string): Promise<ChatListItem> {
  const token = await getAccessToken();
  const res = await fetch(`${API_URL}/api/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title }),
  });

  if (!res.ok) {
    throw new Error('Failed to update chat title');
  }
  return res.json();
}