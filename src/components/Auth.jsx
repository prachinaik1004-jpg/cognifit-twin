import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Auth({ mode, onBack, onSuccess, onSwitchMode }) {
  const [step, setStep] = useState('phone'); // 'phone' | 'otp'
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePhoneSubmit = async (e) => {
    e.preventDefault();
    if (phone.length < 10) {
      setError('Please enter a valid phone number');
      return;
    }
    setError('');
    setLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setLoading(false);
    setStep('otp');
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    if (otp.length < 4) {
      setError('Please enter a valid OTP');
      return;
    }
    setError('');
    setLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setLoading(false);
    onSuccess();
  };

  const handleResendOtp = async () => {
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setLoading(false);
    setError('OTP resent successfully');
    setTimeout(() => setError(''), 3000);
  };

  return (
    <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-teal-50/30 relative overflow-hidden">
      {/* Decorative elements */}
      <motion.div
        animate={{ y: [0, -15, 0] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-16 right-16 w-48 h-48 bg-primary/5 rounded-full blur-3xl"
      />
      <motion.div
        animate={{ y: [0, 15, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-16 left-16 w-64 h-64 bg-teal-500/5 rounded-full blur-3xl"
      />

      <div className="relative z-10 max-w-md mx-auto px-6 w-full">
        <motion.button
          onClick={onBack}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-2 text-sm text-text-muted hover:text-text-main mb-6 cursor-pointer transition-colors"
        >
          <span>←</span>
          <span>Back</span>
        </motion.button>

        {/* Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-3xl shadow-xl shadow-gray-200/50 p-8 border border-gray-100"
        >
          <AnimatePresence mode="wait">
            {step === 'phone' ? (
              <motion.div
                key="phone"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                {/* Icon */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
                  className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-primary to-teal-500 rounded-2xl flex items-center justify-center shadow-lg shadow-primary/20"
                >
                  <span className="text-2xl text-white">📱</span>
                </motion.div>

                <h2 className="font-serif text-3xl text-text-main mb-2 text-center">
                  {mode === 'login' ? 'Welcome back' : 'Get started'}
                </h2>
                <p className="text-sm text-text-muted mb-8 text-center">
                  {mode === 'login'
                    ? 'Enter your phone number to continue'
                    : 'Enter your phone number to create your account'}
                </p>

                <form onSubmit={handlePhoneSubmit} className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-text-main mb-2">
                      Phone Number
                    </label>
                    <div className="relative">
                      <input
                        type="tel"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="+91 98765 43210"
                        className="w-full px-4 py-4 rounded-xl border-2 border-gray-200 focus:border-primary focus:outline-none transition-colors text-text-main bg-gray-50 focus:bg-white"
                      />
                      {phone && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-green-500"
                        >
                          ✓
                        </motion.div>
                      )}
                    </div>
                  </div>

                  {error && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-sm text-red-500 text-center bg-red-50 py-2 rounded-lg"
                    >
                      {error}
                    </motion.p>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full px-4 py-4 rounded-xl bg-gradient-to-r from-primary to-teal-600 text-white font-semibold hover:shadow-lg hover:shadow-primary/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 cursor-pointer relative overflow-hidden"
                  >
                    <span className="relative z-10">
                      {loading ? (
                        <span className="flex items-center justify-center gap-2">
                          <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Sending OTP...
                        </span>
                      ) : (
                        'Send OTP'
                      )}
                    </span>
                  </button>
                </form>

                {mode === 'login' && (
                  <p className="mt-6 text-center text-sm text-text-muted">
                    Don't have an account?{' '}
                    <button
                      onClick={() => onSwitchMode('signup')}
                      className="text-primary font-semibold hover:underline cursor-pointer"
                    >
                      Sign up
                    </button>
                  </p>
                )}
              </motion.div>
            ) : (
              <motion.div
                key="otp"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                {/* Icon */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
                  className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-primary to-teal-500 rounded-2xl flex items-center justify-center shadow-lg shadow-primary/20"
                >
                  <span className="text-2xl text-white">🔐</span>
                </motion.div>

                <h2 className="font-serif text-3xl text-text-main mb-2 text-center">
                  Verify OTP
                </h2>
                <p className="text-sm text-text-muted mb-8 text-center">
                  Enter the 4-digit code sent to{' '}
                  <span className="font-medium text-text-main">{phone}</span>
                </p>

                <form onSubmit={handleOtpSubmit} className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-text-main mb-2">
                      OTP Code
                    </label>
                    <input
                      type="text"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 4))}
                      placeholder="• • • •"
                      maxLength={4}
                      className="w-full px-4 py-4 rounded-xl border-2 border-gray-200 focus:border-primary focus:outline-none transition-colors text-text-main text-center text-3xl tracking-widest font-semibold bg-gray-50 focus:bg-white"
                    />
                  </div>

                  {error && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-sm text-red-500 text-center bg-red-50 py-2 rounded-lg"
                    >
                      {error}
                    </motion.p>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full px-4 py-4 rounded-xl bg-gradient-to-r from-primary to-teal-600 text-white font-semibold hover:shadow-lg hover:shadow-primary/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 cursor-pointer relative overflow-hidden"
                  >
                    <span className="relative z-10">
                      {loading ? (
                        <span className="flex items-center justify-center gap-2">
                          <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Verifying...
                        </span>
                      ) : (
                        'Verify & Continue'
                      )}
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={loading}
                    className="w-full text-sm text-text-muted hover:text-primary font-medium cursor-pointer disabled:opacity-50 transition-colors"
                  >
                    Resend OTP
                  </button>
                </form>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}
