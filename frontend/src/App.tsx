import React, { useState } from 'react';
import { ProfilePage } from './pages/ProfilePage';
import { ExplorePage } from './pages/ExplorePage';
import { ChatPage } from './pages/ChatPage';
import './App.css';

type View = 'profile' | 'explore' | 'chat';

function App() {
  const [currentView, setCurrentView] = useState<View>('profile');
  const [chatPrefill, setChatPrefill] = useState('');

  const handleStartChat = (prefill = '') => {
    setChatPrefill(prefill);
    setCurrentView('chat');
  };

  const handleBackToProfile = () => {
    setCurrentView('profile');
    setChatPrefill('');
  };

  const handleExplore = () => {
    setCurrentView('explore');
  };

  const handleBackFromExplore = () => {
    setCurrentView('profile');
  };

  switch (currentView) {
    case 'chat':
      return <ChatPage onBack={handleBackToProfile} prefill={chatPrefill} />;
    case 'explore':
      return <ExplorePage onBack={handleBackFromExplore} />;
    default:
      return (
        <ProfilePage
          onStartChat={() => handleStartChat()}
          onExplore={handleExplore}
        />
      );
  }
}

export default App;
