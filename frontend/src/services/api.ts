import { supabase } from '@/libs/supabase';


const API_URL = process.env.NEXT_PUBLIC_API_URL;


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
export async function getChatSessions() {
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

export async function createChatSession() {
  const token = await getAccessToken();
  const res = await fetch(`${API_URL}/api/sessions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to create chat session');
  return data;
}

export async function getChatSessionHistory(chatSessionId: string) {
  const token = await getAccessToken();
  const res = await fetch(`${API_URL}/api/sessions/${chatSessionId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error('Failed to get chat session');
  return res.json();
}

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
export async function sendMessage(
  messages: Array<{ role: string, content: string, timestamp: string }>,
    chatSessionId?: string
) {
  const token = await getAccessToken();

  const res = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages,
      session_id: chatSessionId,
      temperature: 0.7,
      max_tokens: 1000,
      stream: false,
    }),
  });

  if (!res.ok) {
    const errText = await res.text();
    console.error('API ERROR:', res.status, errText);
    throw new Error('Failed to send message');
  }
  
  return res.json();
}