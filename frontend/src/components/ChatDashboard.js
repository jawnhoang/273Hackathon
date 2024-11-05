import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './Card';
import '../css/ChatDashboard.css';

const MessageGroup = ({ messages, user }) => {
  const isAI = user === 'AI Assistant';
  
  // Deduplicate messages based on content and timestamp
  const uniqueMessages = messages.reduce((acc, current) => {
    const isDuplicate = acc.find(
      msg => 
        msg.content === current.content && 
        msg.timestamp === current.timestamp
    );
    if (!isDuplicate) {
      acc.push(current);
    }
    return acc;
  }, []);

  return (
    <div className="message-group">
      <div className="message-user-info">
        <div className={`user-avatar ${isAI ? 'user-avatar-ai' : 'user-avatar-human'}`}>
          {user.charAt(0).toUpperCase()}
        </div>
        <div className="user-name">{user}</div>
      </div>
      {uniqueMessages.map((msg, idx) => {
        const messageContent = typeof msg.content === 'object' && msg.content.response 
          ? msg.content.response 
          : msg.content;
          
        return (
          <div key={`${user}-${msg.timestamp}-${idx}`} className="message-wrapper">
            <div className={`message-bubble ${isAI ? 'message-bubble-ai' : 'message-bubble-human'}`}>
              <div className="message-content">{messageContent}</div>
            </div>
            <div className="message-timestamp">
              {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}
            </div>
          </div>
        );
      })}
    </div>
  );
};

const ChatDashboard = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const messageCache = useRef(new Set());

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const websocket = new WebSocket('ws://localhost:8000/ws');

        websocket.onopen = () => {
          console.log('Connected to WebSocket');
          setIsConnected(true);
          setError(null);
        };

        websocket.onmessage = (event) => {
          console.log('Received message:', event.data);
          const message = JSON.parse(event.data);
          const messageContent = typeof message.content === 'object' ? message.content.response : message.content;
          const messageKey = `${message.user}-${messageContent}-${message.timestamp}`;

          if (!messageCache.current.has(messageKey)) {
            messageCache.current.add(messageKey);
            setMessages(prev => [...prev, {
              ...message,
              content: messageContent
            }]);
          }
        };

        websocket.onclose = () => {
          console.log('Disconnected from WebSocket');
          setIsConnected(false);
          setError('Connection lost. Attempting to reconnect...');
          setTimeout(connectWebSocket, 3000);
        };

        setWs(websocket);
      } catch (error) {
        console.error('WebSocket connection error:', error);
        setIsConnected(false);
        setError('Failed to connect to the server. Retrying...');
      }
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    setIsLoading(true);
    setError(null);

    try {
      const timestamp = new Date().toISOString();
      const newMessage = {
        content: input,
        user: 'User',
        timestamp
      };

      const response = await fetch('http://localhost:8000/send_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newMessage),
      });
      const responseData = await response.json();
      console.log('Response from server:', responseData);
      setInput('');
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Group messages by user
  const groupedMessages = messages.reduce((groups, message) => {
    const lastGroup = groups[groups.length - 1];
    
    if (lastGroup && lastGroup.user === message.user) {
      lastGroup.messages.push(message);
    } else {
      groups.push({
        user: message.user,
        messages: [message]
      });
    }
    
    return groups;
  }, []);

  return (
    <div className="chat-container">
      <Card className="chat-card">
        <CardHeader className="chat-header">
          <div className="flex justify-between items-center">
            <CardTitle className="chat-title">SOFI 2023/2024 Chat Assistant</CardTitle>
            <div className={`connection-status ${isConnected ? 'status-connected' : 'status-disconnected'}`}>
              <div className={`status-indicator ${isConnected ? 'indicator-connected' : 'indicator-disconnected'}`} />
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <div className="messages-container">
            {error && (
              <div className="error-alert">
                <div className="error-icon">⚠</div>
                <div>{error}</div>
              </div>
            )}
            
            {groupedMessages.map((group, idx) => (
              <MessageGroup 
                key={`${group.user}-${idx}`}
                messages={group.messages} 
                user={group.user} 
              />
            ))}
            
            <div ref={messagesEndRef} />
          </div>

          <div className="input-container">
            <div className="input-wrapper">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask about SOFI 2023/2024 data..."
                disabled={isLoading}
                className="chat-input"
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className={`send-button ${!input.trim() || isLoading ? 'send-button-disabled' : 'send-button-enabled'}`}
              >
                {isLoading ? '⟳' : '→'}
                Send
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatDashboard;