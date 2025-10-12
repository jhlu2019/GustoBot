import React from 'react'
import ChatInterface from './components/ChatInterface'
import ErrorBoundary from './components/ErrorBoundary'
import './App.css'

function App() {
  return (
    <ErrorBoundary>
      <div className="App">
        <header className="app-header">
          <div className="header-content">
            <h1>🍳 GustoBot</h1>
            <p className="header-subtitle">您的智能菜谱助手</p>
            <p className="header-description">
              基于Multi-Agent架构 · RAG知识检索 · 智能对话
            </p>
          </div>
        </header>
        <main className="app-main">
          <ChatInterface />
        </main>
        <footer className="app-footer">
          <p>
            Powered by{' '}
            <a
              href="https://github.com/yourusername/GustoBot"
              target="_blank"
              rel="noopener noreferrer"
            >
              Multi-Agent AI
            </a>{' '}
            · Milvus · OpenAI · Cohere
          </p>
        </footer>
      </div>
    </ErrorBoundary>
  )
}

export default App
