import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  HiPaperAirplane,
  HiPlus,
  HiMicrophone,
  HiClipboardDocumentList,
  HiExclamationTriangle,
  HiBeaker,
  HiDocumentText,
} from 'react-icons/hi2';
import { sendChatMessage, fetchChatHistory } from '../services/chat';

const quickActions = [
  { id: 'meal', label: 'Log Meal', icon: HiClipboardDocumentList, color: 'text-amber-600 bg-amber-50' },
  { id: 'risks', label: 'View Health Risks', icon: HiExclamationTriangle, color: 'text-rose-600 bg-rose-50' },
  { id: 'simulate', label: 'Run What-If Simulation', icon: HiBeaker, color: 'text-primary bg-primary-light' },
  { id: 'summary', label: 'View Summary', icon: HiDocumentText, color: 'text-indigo-600 bg-indigo-50' },
];

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good Morning';
  if (hour < 17) return 'Good Afternoon';
  return 'Good Evening';
}

function getEmotionStyles(emotion) {
  const emotionStyles = {
    happy: 'bg-green-50 text-green-900 rounded-bl-md border border-green-200',
    sad: 'bg-blue-50 text-blue-900 rounded-bl-md border border-blue-200',
    anxious: 'bg-amber-50 text-amber-900 rounded-bl-md border border-amber-200',
    angry: 'bg-red-50 text-red-900 rounded-bl-md border border-red-200',
    neutral: 'bg-gray-50 text-text-main rounded-bl-md border border-gray-200',
    calm: 'bg-teal-50 text-teal-900 rounded-bl-md border border-teal-200',
    excited: 'bg-purple-50 text-purple-900 rounded-bl-md border border-purple-200',
  };
  return emotionStyles[emotion] || emotionStyles.neutral;
}

export default function ChatWindow({ isSimulationMode = false, switchView, user }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [showSimBanner, setShowSimBanner] = useState(isSimulationMode);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const isLanding = messages.length === 0;

  useEffect(() => {
    if (!isLanding) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLanding]);

  useEffect(() => {
    async function loadHistory() {
      try {
        const response = await fetchChatHistory(user?.id, 'chat');
        if (response.history && response.history.length > 0) {
          const formattedMessages = response.history.map(turn => ({
            role: turn.role,
            content: turn.content,
          })).reverse(); // Reverse to show newest first
          setMessages(formattedMessages);
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    }
    loadHistory();
  }, [user?.id]);

  const handleSend = async (overrideInput) => {
    const trimmed = (overrideInput ?? input).trim();
    if (!trimmed) return;

    const userMsg = { role: 'user', content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage(trimmed, user?.id);
      const assistantMsg = {
        role: 'assistant',
        content: response.reply,
        emotion: response.emotion,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      console.error('Error sending message:', error);
      const fallbackMsg = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        emotion: 'neutral',
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickAction = (action) => {
    if (action.id === 'qr') {
      switchView?.('QR');
      return;
    }
    if (action.id === 'simulate') {
      switchView?.('What-If');
      setShowSimBanner(true);
      const simMsg = { role: 'user', content: 'Run a What-If Simulation' };
      const simReply = {
        role: 'assistant',
        content: "Simulation mode activated. Ask me 'what if' questions about lifestyle changes and their projected impact on your cognitive health.",
      };
      setMessages([simMsg, simReply]);
      return;
    }
    if (action.id === 'meal') {
      handleSend('Log my latest meal');
      return;
    }
    if (action.id === 'risks') {
      handleSend('Show me my current health risks');
      return;
    }
  };

  return (
    <div className="flex flex-col relative max-w-4xl mx-auto w-full h-[calc(100vh-4rem)]">
      {showSimBanner && !isLanding && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-primary-light border-b border-primary/20 px-3 py-1.5 text-center shrink-0"
        >
          <span className="text-xs font-medium text-primary">
            Simulation Mode - Explore hypothetical scenarios
          </span>
        </motion.div>
      )}

      {/* Chat State Header */}
      {!isLanding && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="px-4 py-2 border-b border-gray-100 shrink-0"
        >
          <h2 className="font-serif text-lg text-text-main">
            {getGreeting()}, {user?.name?.split(' ')[0] || 'there'}
          </h2>
        </motion.div>
      )}

      {/* Main Content Area */}
      <div className={`flex-1 overflow-y-auto ${isLanding ? 'flex flex-col items-center justify-center' : ''} scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent hover:scrollbar-thumb-gray-400`}>
        <AnimatePresence mode="wait">
          {isLanding ? (
            <motion.div
              key="landing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
              className="flex flex-col items-center w-full max-w-2xl px-4"
            >
              <h1 className="font-serif text-4xl sm:text-5xl text-text-main mb-2 text-center">
                {getGreeting()}, {user?.name?.split(' ')[0] || 'there'}
              </h1>
              <p className="text-text-muted text-sm mb-10 text-center">
                How can I help you with your cognitive health today?
              </p>

              {/* Quick Action Grid */}
              <div className="grid grid-cols-2 gap-3 w-full max-w-md mb-10">
                {quickActions.map((action) => {
                  const Icon = action.icon;
                  return (
                    <button
                      key={action.id}
                      onClick={() => handleQuickAction(action)}
                      className="flex items-center gap-3 px-4 py-3 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 hover:border-gray-300 transition-all text-left cursor-pointer group"
                    >
                      <div className={`p-2 rounded-lg ${action.color}`}>
                        <Icon className="text-base" />
                      </div>
                      <span className="text-sm text-text-main font-medium group-hover:text-text-main">
                        {action.label}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Floating Input — Centered in Landing */}
              <div className="w-full max-w-2xl">
                <FloatingInput
                  input={input}
                  setInput={setInput}
                  handleSend={handleSend}
                  handleKeyDown={handleKeyDown}
                  isSimulationMode={showSimBanner}
                  isLoading={isLoading}
                />
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="chat"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
              className="max-w-2xl mx-auto w-full px-3 py-3 space-y-3"
            >
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25, delay: i === messages.length - 1 ? 0.1 : 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed
                      ${
                        msg.role === 'user'
                          ? 'bg-primary text-white rounded-br-md'
                          : getEmotionStyles(msg.emotion)
                      }`}
                  >
                    {msg.content}
                  </div>
                </motion.div>
              ))}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="bg-gray-50 text-text-main rounded-2xl rounded-bl-md border border-gray-200 px-4 py-3 text-sm">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Floating Input — Pinned to Bottom in Chat State */}
      {!isLanding && (
        <div className="shrink-0 border-t border-gray-100 bg-white">
          <div className="max-w-2xl mx-auto px-3 py-2">
            <FloatingInput
              input={input}
              setInput={setInput}
              handleSend={handleSend}
              handleKeyDown={handleKeyDown}
              isSimulationMode={showSimBanner}
              isLoading={isLoading}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function FloatingInput({ input, setInput, handleSend, handleKeyDown, isSimulationMode, isLoading }) {
  return (
    <div className="flex items-center gap-2 rounded-2xl border border-gray-200 bg-white shadow-sm px-3 py-2 transition-shadow focus-within:shadow-md focus-within:border-gray-300">
      <button className="p-1 rounded-lg text-text-muted hover:bg-gray-100 hover:text-text-main transition-colors cursor-pointer">
        <HiPlus className="text-base" />
      </button>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={
          isSimulationMode
            ? "Ask a 'what-if' question..."
            : 'Message your Cognitive Health Twin...'
        }
        disabled={isLoading}
        className="flex-1 text-sm text-text-main placeholder:text-text-muted bg-transparent focus:outline-none min-w-0 disabled:opacity-50"
      />
      <button className="p-1 rounded-lg text-text-muted hover:bg-gray-100 hover:text-text-main transition-colors cursor-pointer">
        <HiMicrophone className="text-base" />
      </button>
      <button
        onClick={() => handleSend()}
        disabled={!input.trim() || isLoading}
        className="p-1 rounded-lg bg-primary text-white hover:bg-primary-hover disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
      >
        {isLoading ? (
          <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <HiPaperAirplane className="text-sm" />
        )}
      </button>
    </div>
  );
}
