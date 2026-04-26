import { useState, useEffect, useRef } from 'react';
import { ProactiveInsight } from '../types';

export function useWebSocket(userId: string) {
  const [notifications, setNotifications] = useState<ProactiveInsight[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!userId) return;

    let reconnectTimer: ReturnType<typeof setTimeout>;
    let backoff = 1000;

    const connect = () => {
      // In dev, Vite proxies /ws to ws://localhost:8080/ws
      // Using relative URL or absolute based on location
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/notifications/${userId}`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        backoff = 1000; // reset
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'proactive_insight') {
            setNotifications(prev => [...prev, data]);
          }
        } catch (e) {
          console.error('Failed to parse WS message', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // auto-reconnect
        reconnectTimer = setTimeout(connect, backoff);
        backoff = Math.min(backoff * 1.5, 10000); // max 10s
      };
      
      ws.onerror = (e) => {
         console.error('WS error', e);
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [userId]);

  const removeNotification = (timestamp: number) => {
    setNotifications(prev => prev.filter(n => n.timestamp !== timestamp));
  };

  return {
    notifications,
    isConnected,
    removeNotification
  };
}
