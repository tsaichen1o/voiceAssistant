import ChatInterface from '@/components/ChatInterface';

interface PageProps {
  params: Promise<{ userId: string; sessionId: string }>;
}

export default async function Page({ params }: PageProps) {
  const { userId, sessionId } = await params;

  if (!userId || !sessionId) {
    return <div>Invalid chat session.</div>;
  }

  return <ChatInterface userId={userId} sessionId={sessionId} />;
}