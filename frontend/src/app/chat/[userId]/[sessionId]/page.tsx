import ChatInterface from '@/components/ChatInterface';


interface ChatPageProps {
  params: {
    userId: string;
    sessionId: string;
  };
}

export default async function ChatPage({ params }: ChatPageProps) {
  const { userId, sessionId } = await params;

  if (!userId || !sessionId) {
    return <div>Invalid chat session.</div>;
  }

  return <ChatInterface userId={userId} sessionId={sessionId} />;
}