import ChatInterface from '@/components/ChatInterface';


interface PageProps {
  params: Promise<{ userId: string; chatSessionId: string }>;
}

export default async function Page({ params }: PageProps) {
  const { userId, chatSessionId } = await params;

  if (!userId || !chatSessionId) {
    return <div>Invalid chat session.</div>;
  }

  return <ChatInterface chatSessionId={chatSessionId} />;
}