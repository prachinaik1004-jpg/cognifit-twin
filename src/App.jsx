import { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import InsightsView from './components/InsightsView';
import SimulationUI from './components/SimulationUI';
import QRView from './components/QRView';
import LandingPage from './components/LandingPage';
import Auth from './components/Auth';
import Onboarding from './components/Onboarding';

const viewMap = {
  Chat: ChatWindow,
  Insights: InsightsView,
  'What-If': SimulationUI,
  QR: QRView,
};

function App() {
  const [appState, setAppState] = useState('landing'); // 'landing' | 'auth' | 'onboarding' | 'main'
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'signup'
  const [currentView, setCurrentView] = useState('Chat');

  const switchView = (view) => setCurrentView(view);
  const ActiveView = viewMap[currentView] || ChatWindow;

  const handleLoginClick = () => {
    setAuthMode('login');
    setAppState('auth');
  };

  const handleSignUpClick = () => {
    setAuthMode('signup');
    setAppState('auth');
  };

  const handleAuthSuccess = () => {
    // Only show onboarding for first-time signup, not for returning login
    if (authMode === 'signup') {
      setAppState('onboarding');
    } else {
      setAppState('main');
    }
  };

  const handleOnboardingComplete = (userData) => {
    console.log('Onboarding complete:', userData);
    setAppState('main');
  };

  const handleAuthBack = () => {
    setAppState('landing');
  };

  const handleOnboardingBack = () => {
    setAppState('landing');
  };

  const handleSwitchAuthMode = (mode) => {
    setAuthMode(mode);
  };

  // Landing, Auth, and Onboarding states don't show Sidebar
  if (appState === 'landing') {
    return <LandingPage onLoginClick={handleLoginClick} onSignUpClick={handleSignUpClick} />;
  }

  if (appState === 'auth') {
    return (
      <Auth
        mode={authMode}
        onBack={handleAuthBack}
        onSuccess={handleAuthSuccess}
        onSwitchMode={handleSwitchAuthMode}
      />
    );
  }

  if (appState === 'onboarding') {
    return <Onboarding onComplete={handleOnboardingComplete} onBack={handleOnboardingBack} />;
  }

  // Main app state with Sidebar and profile header
  return (
    <>
      <Sidebar currentView={currentView} onNavigate={setCurrentView} />
      <main className="flex-1 min-h-screen bg-white overflow-hidden flex flex-col">
        {/* Profile Header — Visible on all views */}
        <div className="h-16 border-b border-gray-100 flex items-center justify-end px-6 shrink-0">
          <button className="w-9 h-9 rounded-full bg-orange-500 text-white font-semibold text-sm flex items-center justify-center hover:bg-orange-600 transition-colors cursor-pointer">
            P
          </button>
        </div>
        <ActiveView key={currentView} switchView={switchView} />
      </main>
    </>
  );
}

export default App;
