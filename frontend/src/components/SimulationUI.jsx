import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HiBeaker, HiArrowPath, HiChartBar, HiSparkles } from 'react-icons/hi2';
import { fetchChatHistory } from '../services/chat';

export default function SimulationUI({ switchView, user }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isSimulating, setIsSimulating] = useState(false);
  const messagesEndRef = useRef(null);
  const isLanding = messages.length === 0;

  useEffect(() => {
    if (!isLanding) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLanding]);

  // Load what-if simulation history on mount
  useEffect(() => {
    async function loadHistory() {
      try {
        const response = await fetchChatHistory(user?.id, 'whatif');
        if (response.history && response.history.length > 0) {
          const formattedMessages = response.history.map(turn => ({
            role: turn.role,
            content: turn.content,
          })).reverse();
          setMessages(formattedMessages);
        }
      } catch (error) {
        console.error('Failed to load simulation history:', error);
      }
    }
    loadHistory();
  }, [user?.id]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    const userMsg = { role: 'user', content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsSimulating(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          user_id: user?.id || '00000000-0000-0000-0000-000000000001',
          view: 'whatif'
        })
      });
      const data = await response.json();

      const reply = {
        role: 'assistant',
        content: data.reply || 'Simulation failed',
      };
      setMessages((prev) => [...prev, reply]);
    } catch (error) {
      console.error('Simulation error:', error);
      const reply = {
        role: 'assistant',
        content: 'Sorry, there was an error running the simulation. Please try again.',
      };
      setMessages((prev) => [...prev, reply]);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const runPresetSimulation = (preset) => {
    setInput(preset);
    setTimeout(() => handleSend(), 100);
  };

  return (
    <div className="flex flex-col flex-1 bg-gradient-to-br from-slate-50 to-blue-50/30">
      {/* Simulation Banner */}
      <div className="bg-gradient-to-r from-primary/10 to-blue-50 border-b border-primary/20 px-6 py-3">
        <div className="flex items-center gap-2 max-w-4xl mx-auto">
          <HiBeaker className="text-primary text-lg" />
          <span className="text-sm font-medium text-primary">
            What-If Simulation Lab — Explore hypothetical scenarios
          </span>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          {isLanding ? (
            <motion.div
              key="landing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
              className="max-w-3xl mx-auto px-6 py-12"
            >
              <div className="text-center mb-10">
                <h1 className="text-3xl font-semibold text-text-main mb-3">
                  What-If Simulation Lab
                </h1>
                <p className="text-text-muted text-sm max-w-md mx-auto">
                  Test how lifestyle changes might impact your cognitive health over time
                </p>
              </div>

              {/* Preset Simulations */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
                {[
                  { label: 'What if I sleep 8 hours daily?', icon: HiSparkles },
                  { label: 'Impact of daily meditation', icon: HiChartBar },
                  { label: 'Exercise 3x per week effect', icon: HiArrowPath },
                  { label: 'Reducing caffeine intake', icon: HiBeaker },
                ].map((preset, i) => (
                  <button
                    key={i}
                    onClick={() => runPresetSimulation(preset.label)}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 hover:border-gray-300 transition-all text-left cursor-pointer group"
                  >
                    <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                      <preset.icon className="text-base" />
                    </div>
                    <span className="text-sm text-text-main font-medium">
                      {preset.label}
                    </span>
                  </button>
                ))}
              </div>

              {/* Simulation Input */}
              <div className="max-w-2xl mx-auto">
                <div className="flex items-center gap-2 rounded-2xl border border-gray-200 bg-white shadow-sm px-4 py-3">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask a what-if question..."
                    className="flex-1 text-sm text-text-main placeholder:text-text-muted bg-transparent focus:outline-none min-w-0"
                  />
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || isSimulating}
                    className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer text-sm font-medium flex items-center gap-2"
                  >
                    {isSimulating ? (
                      <>
                        <HiArrowPath className="animate-spin text-base" />
                        Simulating...
                      </>
                    ) : (
                      'Run Simulation'
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="chat"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
              className="max-w-3xl mx-auto px-6 py-8 space-y-4"
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
                    className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap
                      ${
                        msg.role === 'user'
                          ? 'bg-primary text-white rounded-br-md'
                          : 'bg-white text-text-main rounded-bl-md border border-gray-200 shadow-sm'
                      }`}
                  >
                    {msg.content}
                  </div>
                </motion.div>
              ))}
              <div ref={messagesEndRef} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input at Bottom in Chat State */}
      {!isLanding && (
        <div className="shrink-0 border-t border-gray-200 bg-white/80 backdrop-blur-sm">
          <div className="max-w-3xl mx-auto px-6 py-4">
            <div className="flex items-center gap-2 rounded-2xl border border-gray-200 bg-white shadow-sm px-4 py-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Run another simulation..."
                className="flex-1 text-sm text-text-main placeholder:text-text-muted bg-transparent focus:outline-none min-w-0"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isSimulating}
                className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer text-sm font-medium flex items-center gap-2"
              >
                {isSimulating ? (
                  <>
                    <HiArrowPath className="animate-spin text-base" />
                    Simulating...
                  </>
                ) : (
                  'Run Simulation'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
