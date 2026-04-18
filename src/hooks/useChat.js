import { useState } from 'react';

export default function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (content) => {
    const userMsg = { role: 'user', content };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // TODO: Replace with actual API call via services/chat.js
    setTimeout(() => {
      const reply = {
        role: 'assistant',
        content: 'Placeholder response — connect to your AI backend here.',
      };
      setMessages((prev) => [...prev, reply]);
      setIsLoading(false);
    }, 800);
  };

  const clearChat = () => setMessages([]);

  return { messages, isLoading, sendMessage, clearChat };
}
