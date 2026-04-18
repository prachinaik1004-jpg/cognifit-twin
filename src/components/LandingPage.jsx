import { motion } from 'framer-motion';

export default function LandingPage({ onLoginClick, onSignUpClick }) {
  return (
    <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-teal-50/30 relative overflow-hidden">
      {/* Decorative floating elements */}
      <motion.div
        animate={{ y: [0, -20, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-20 left-20 w-64 h-64 bg-primary/5 rounded-full blur-3xl"
      />
      <motion.div
        animate={{ y: [0, 20, 0] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-20 right-20 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl"
      />
      <motion.div
        animate={{ scale: [1, 1.1, 1] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-500/3 rounded-full blur-3xl"
      />

      <div className="relative z-10 max-w-3xl mx-auto px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          {/* Logo/Icon */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="w-20 h-20 mx-auto mb-8 bg-gradient-to-br from-primary to-teal-500 rounded-2xl flex items-center justify-center shadow-lg shadow-primary/20"
          >
            <span className="text-3xl text-white font-bold">C</span>
          </motion.div>

          <h1 className="font-serif text-6xl text-text-main mb-6 leading-tight">
            Welcome to<br />
            <span className="bg-gradient-to-r from-primary to-teal-600 bg-clip-text text-transparent">
              Cognifit Twin
            </span>
          </h1>
          <p className="text-xl text-text-muted mb-12 max-w-lg mx-auto leading-relaxed">
            Your personal AI-powered digital health twin. Understand your cognitive health like never before.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <button
            onClick={onLoginClick}
            className="group px-8 py-4 rounded-2xl border-2 border-gray-200 text-text-main font-semibold hover:border-primary hover:text-primary transition-all duration-300 cursor-pointer relative overflow-hidden"
          >
            <span className="relative z-10">Login</span>
            <motion.div
              className="absolute inset-0 bg-primary/5 translate-y-full group-hover:translate-y-0 transition-transform duration-300"
            />
          </button>
          <button
            onClick={onSignUpClick}
            className="group px-8 py-4 rounded-2xl bg-gradient-to-r from-primary to-teal-600 text-white font-semibold hover:shadow-lg hover:shadow-primary/30 transition-all duration-300 cursor-pointer relative overflow-hidden"
          >
            <span className="relative z-10">Sign Up</span>
            <motion.div
              className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"
            />
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="mt-16 flex flex-col sm:flex-row gap-8 justify-center text-sm text-text-muted"
        >
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
              <span className="text-green-600">✓</span>
            </div>
            <span>AI-Powered Insights</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
              <span className="text-blue-600">✓</span>
            </div>
            <span>Wearable Integration</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
              <span className="text-purple-600">✓</span>
            </div>
            <span>Personalized Health Plans</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
