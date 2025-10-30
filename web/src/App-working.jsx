import React, { useState } from 'react';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '你好！我是GustoBot智能菜谱助手。请问有什么可以帮助你的吗？' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          session_id: 'test-session'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.answer,
          route: data.metadata?.route
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: '抱歉，我现在无法回应。请稍后再试。'
        }]);
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '连接失败。请确保后端服务正在运行。'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        background: 'white',
        borderRadius: '20px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        overflow: 'hidden',
        height: '80vh',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span style={{ fontSize: '30px' }}>🍳</span>
          <div>
            <h1 style={{ margin: 0, fontSize: '20px' }}>GustoBot</h1>
            <p style={{ margin: 0, fontSize: '14px', opacity: 0.9 }}>智能菜谱助手</p>
          </div>
        </div>

        {/* Messages */}
        <div style={{
          flex: 1,
          padding: '20px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
            }}>
              <div style={{
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                  : '#f0f0f0',
                color: msg.role === 'user' ? 'white' : '#333',
                padding: '10px 15px',
                borderRadius: '15px',
                maxWidth: '70%',
                wordBreak: 'break-word'
              }}>
                {msg.content}
                {msg.route && (
                  <div style={{
                    fontSize: '11px',
                    opacity: 0.7,
                    marginTop: '5px',
                    padding: '2px 8px',
                    background: 'rgba(255,255,255,0.2)',
                    borderRadius: '10px',
                    display: 'inline-block'
                  }}>
                    路由: {msg.route}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{
                background: '#f0f0f0',
                padding: '10px 15px',
                borderRadius: '15px',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}>
                <span>思考中</span>
                <span>⏳</span>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div style={{
          padding: '20px',
          borderTop: '1px solid #eee',
          display: 'flex',
          gap: '10px'
        }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="输入消息..."
            style={{
              flex: 1,
              padding: '10px 15px',
              border: '1px solid #ddd',
              borderRadius: '20px',
              outline: 'none',
              fontSize: '16px'
            }}
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            style={{
              padding: '10px 20px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '20px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '16px'
            }}
          >
            发送
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;