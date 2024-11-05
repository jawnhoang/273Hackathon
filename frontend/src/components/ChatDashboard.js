import React, { useState, useEffect, useRef } from 'react';

const ChatDashboard = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);

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
        };

        websocket.onmessage = (event) => {
          const message = JSON.parse(event.data);
          setMessages(prev => [...prev, message]);
        };

        websocket.onclose = () => {
          console.log('Disconnected from WebSocket');
          setIsConnected(false);
          setTimeout(connectWebSocket, 3000);
        };

        setWs(websocket);
      } catch (error) {
        console.error('WebSocket connection error:', error);
        setIsConnected(false);
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

    try {
      await fetch('http://localhost:8000/send_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: input,
          user: 'User',
        }),
      });

      // Optionally add the message to the local state immediately
      setMessages(prev => [...prev, {
        content: input,
        user: 'User',
        timestamp: new Date().toISOString()
      }]);
      
      setInput('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md">
        {/* Header */}
        <div className="border-b p-4 flex justify-between items-center">
          <h1 className="text-xl font-bold">Chat Dashboard</h1>
          <div className={`flex items-center gap-2 text-sm ${
            isConnected ? 'text-green-600' : 'text-red-600'
          }`}>
            <div className={`h-2 w-2 rounded-full ${
              isConnected ? 'bg-green-600' : 'bg-red-600'
            }`} />
            {isConnected ? 'Connected' : 'Disconnecting...'}
          </div>
        </div>

        {/* Messages */}
        <div className="h-[calc(100vh-250px)] overflow-y-auto p-4 bg-gray-50">
          {messages.map((msg, idx) => (
            <div key={idx} className="mb-4 bg-white p-4 rounded-lg shadow-sm">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                  {msg.user.charAt(0).toUpperCase()}
                </div>
                <div className="font-bold text-gray-800">{msg.user}</div>
              </div>
              <div className="ml-10 mt-2 text-gray-700">{msg.content}</div>
              {msg.context && (
                <div className="ml-10 mt-2 p-3 bg-gray-50 rounded-md">
                  <div className="text-sm font-semibold text-gray-600">Related Context:</div>
                  {msg.context.map((ctx, cidx) => (
                    <div key={cidx} className="ml-2 mt-1 text-sm text-gray-600">
                      {ctx}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Type your message..."
              className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim()}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                !input.trim()
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatDashboard;