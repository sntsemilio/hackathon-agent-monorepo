import { useState, useMemo } from 'react';
import { USERS } from './data/users';
import { TopBar } from './components/TopBar';
// Column placeholders
import { TracePanel } from './components/trace/TracePanel';
import { ChatPanel } from './components/chat/ChatPanel';
import { ProfilePanel } from './components/profile/ProfilePanel';
import { NotificationToast } from './components/notifications/NotificationToast';

import { useSSEChat } from './hooks/useSSEChat';
import { useWebSocket } from './hooks/useWebSocket';
import { useSpeechRecognition } from './hooks/useSpeechRecognition';

export default function App() {
  const [selectedUserId, setSelectedUserId] = useState(USERS[0].id);
  const [personalizationEnabled, setPersonalizationEnabled] = useState(true);
  
  // A simple session ID to group traces/messages per page load
  const [sessionId] = useState(`sess-${Math.random().toString(36).substring(2, 10)}`);

  const selectedUser = useMemo(() => 
    USERS.find(u => u.id === selectedUserId) || USERS[0],
  [selectedUserId]);

  const {
    messages,
    traces,
    isStreaming,
    sendMessage,
    pendingToolCall,
    confirmToolCall,
    ficha,
  } = useSSEChat({
    userId: selectedUser.id,
    sessionId,
    personalizationEnabled,
  });

  const { notifications, removeNotification } = useWebSocket(selectedUser.id);
  const speech = useSpeechRecognition();

  return (
    <div className="min-h-screen bg-background flex flex-col font-sans overflow-hidden">
      <TopBar 
        selectedUser={selectedUser} 
        onUserChange={setSelectedUserId}
        personalizationEnabled={personalizationEnabled}
        onPersonalizationToggle={setPersonalizationEnabled}
      />

      <main className="flex-1 overflow-hidden">
        <div className="h-full grid grid-cols-1 lg:grid-cols-[320px_1fr_340px] gap-0">
          
          {/* Left Column: Trace Panel */}
          <aside className="border-r border-border bg-card/50 overflow-hidden hidden lg:block">
            <TracePanel traces={traces} />
          </aside>

          {/* Center Column: Chat */}
          <section className="h-full flex flex-col overflow-hidden relative">
            <ChatPanel 
              user={selectedUser}
              messages={messages}
              isStreaming={isStreaming}
              onSendMessage={sendMessage}
              pendingToolCall={pendingToolCall}
              onConfirmToolCall={confirmToolCall}
              speech={speech}
            />
          </section>

          {/* Right Column: Profile Panel */}
          <aside className="border-l border-border bg-card/50 overflow-hidden hidden lg:block">
            <ProfilePanel user={selectedUser} ficha={ficha} />
          </aside>

        </div>
      </main>

      {/* Global Notifications overlay */}
      <div className="fixed top-20 right-6 z-50 flex flex-col gap-2">
        {notifications.map((notif) => (
          <NotificationToast 
            key={notif.timestamp} 
            notification={notif} 
            onDismiss={() => removeNotification(notif.timestamp)} 
          />
        ))}
      </div>
    </div>
  );
}
