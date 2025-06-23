'use client';


export const ThinkingIndicator = ({ isDarkMode }: { isDarkMode: boolean }) => {
  return (
    <div className={`flex items-center space-x-2 p-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
      <span className="text-sm font-medium">Assistant is thinking...</span>
    </div>
  );
};