import React from 'react';

function App() {
  return (
    <div style={{ padding: '20px', minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      <div style={{ background: 'white', padding: '30px', borderRadius: '10px', maxWidth: '600px', margin: '50px auto' }}>
        <h1 style={{ textAlign: 'center', color: '#333' }}>🍳 GustoBot</h1>
        <p style={{ textAlign: 'center', fontSize: '18px', color: '#666' }}>
          智能菜谱助手正在运行...
        </p>
        <div style={{ background: '#f0f0f0', padding: '15px', borderRadius: '5px', margin: '20px 0' }}>
          <h3>服务状态:</h3>
          <p>✅ 前端服务正常运行</p>
          <p>✅ React 组件已加载</p>
          <p>端口: {window.location.port}</p>
        </div>
      </div>
    </div>
  );
}

export default App;