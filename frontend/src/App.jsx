import { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import InsightsView from './components/InsightsView';
import SimulationUI from './components/SimulationUI';
import SummaryView from './components/SummaryView';
import Settings from './components/Settings';
import LandingPage from './components/LandingPage';
import Auth from './components/Auth';
import Onboarding from './components/Onboarding';
import { handleCallback } from './services/wearable';

const viewMap = {
  Chat: ChatWindow,
  Insights: InsightsView,
  'What-If': SimulationUI,
  Summary: SummaryView,
  Settings: Settings,
};

function App() {
  const [appState, setAppState] = useState('landing'); // 'landing' | 'auth' | 'onboarding' | 'main'
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'signup'
  const [currentView, setCurrentView] = useState('Chat');
  const [user, setUser] = useState(null);
  const processedCodeRef = useRef(false);

  // Load user session on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('cognifit_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      setAppState('main');
    }

    // Handle Google OAuth callback - only once
    if (processedCodeRef.current) return;
    
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    
    console.log('OAuth callback check - code:', code, 'user:', savedUser ? JSON.parse(savedUser).id : 'none');
    
    if (code && savedUser && !processedCodeRef.current) {
      processedCodeRef.current = true;
      console.log('Exchanging code for tokens...');
      // Exchange code for tokens
      handleCallback(code, JSON.parse(savedUser).id)
        .then((result) => {
          console.log('Token exchange result:', result);
          // Clear URL parameters and redirect to Settings
          window.history.replaceState({}, document.title, window.location.pathname);
          setCurrentView('Settings');
        })
        .catch((error) => {
          console.error('OAuth callback error:', error);
        });
    }
  }, []);

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

  const handleAuthSuccess = (userData = null) => {
    if (userData) {
      // For returning login with existing user data
      setUser(userData);
      localStorage.setItem('cognifit_user', JSON.stringify(userData));
      setAppState('main');
    } else if (authMode === 'signup') {
      setAppState('onboarding');
    } else {
      setAppState('main');
    }
  };

  const handleOnboardingComplete = async (userData) => {
    console.log('Onboarding complete:', userData);
    try {
      // Save user to backend
      const response = await fetch('http://localhost:8000/api/user/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_data: userData })
      });
      const result = await response.json();
      
      if (result.success) {
        const newUser = {
          id: result.user_id,
          name: userData.name,
          ...userData
        };
        setUser(newUser);
        localStorage.setItem('cognifit_user', JSON.stringify(newUser));
        setAppState('main');
      }
    } catch (error) {
      console.error('Registration error:', error);
      // Still proceed to main app even if registration fails
      setAppState('main');
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('cognifit_user');
    setAppState('landing');
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
        <div className="h-16 border-b border-gray-100 flex items-center justify-between px-6 shrink-0">
          <div className="font-serif text-xl text-text-main">
            {user?.name ? `Hello, ${user.name.split(' ')[0]}` : 'Welcome'}
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={handleLogout}
              className="text-sm text-text-muted hover:text-text-main cursor-pointer transition-colors"
            >
              Logout
            </button>
            <button className="w-9 h-9 rounded-full bg-orange-500 text-white font-semibold text-sm flex items-center justify-center hover:bg-orange-600 transition-colors cursor-pointer">
              {user?.name ? user.name.charAt(0).toUpperCase() : 'P'}
            </button>
          </div>
        </div>
        <ActiveView key={currentView} switchView={switchView} user={user} />
      </main>
    </>
  );
}

export default App;
