import React, { useState, useRef, useEffect } from 'react'
import { sendMessage } from '../services/api'
import Message from './Message'
import QuickActions from './QuickActions'
import StatsPanel from './StatsPanel'
import { Send, Loader } from 'lucide-react'
import './ChatInterface.css'

function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      content: '您好！我是GustoBot，您的智能菜谱助手。🍳\n\n您可以问我：\n- 如何制作某道菜\n- 推荐菜谱\n- 烹饪技巧\n- 食材搭配\n\n试试下面的快速问题，或者直接输入您的问题！',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const [showStats, setShowStats] = useState(false)
  const [showQuickActions, setShowQuickActions] = useState(true)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessageToBot = async (messageText) => {
    if (!messageText.trim() || loading) return

    const userMessage = {
      type: 'user',
      content: messageText.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setShowQuickActions(false)

    try {
      const response = await sendMessage({
        message: userMessage.content,
        session_id: sessionId
      })

      const botMessage = {
        type: 'bot',
        content: response.answer || '抱歉，我没有收到回复。',
        timestamp: new Date(),
        metadata: response.metadata
      }

      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      const errorMessage = {
        type: 'bot',
        content: '抱歉，服务暂时不可用。请检查后端服务是否正常运行，或稍后再试。',
        timestamp: new Date(),
        error: true
      }
      setMessages(prev => [...prev, errorMessage])
      console.error('Chat error:', error)
    } finally {
      setLoading(false)
      // 聚焦输入框
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    await sendMessageToBot(input)
  }

  const handleQuickQuestion = (question) => {
    sendMessageToBot(question)
  }

  const handleClearChat = () => {
    if (window.confirm('确定要清空对话记录吗？')) {
      setMessages([
        {
          type: 'bot',
          content: '对话已清空。有什么新问题吗？',
          timestamp: new Date()
        }
      ])
      setShowQuickActions(true)
      setInput('')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="chat-interface">
      <div className="chat-messages">
        {showQuickActions && (
          <QuickActions
            onQuickQuestion={handleQuickQuestion}
            onClearChat={handleClearChat}
            onShowStats={() => setShowStats(true)}
            disabled={loading}
          />
        )}

        {messages.map((msg, index) => (
          <Message key={index} message={msg} />
        ))}

        {loading && (
          <div className="message bot-message">
            <div className="message-avatar">
              <div className="avatar bot-avatar">
                <Loader size={20} className="spin-animation" />
              </div>
            </div>
            <div className="message-wrapper">
              <div className="message-header">
                <span className="message-sender">GustoBot</span>
              </div>
              <div className="message-content loading">
                <span className="typing-text">正在思考</span>
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="输入您的问题... (按 Enter 发送)"
          className="chat-input"
          disabled={loading}
          autoFocus
        />
        <button
          type="submit"
          className="chat-send-button"
          disabled={loading || !input.trim()}
          title="发送消息"
        >
          {loading ? (
            <Loader size={20} className="spin-animation" />
          ) : (
            <Send size={20} />
          )}
        </button>
      </form>

      <StatsPanel
        isOpen={showStats}
        onClose={() => setShowStats(false)}
      />
    </div>
  )
}

export default ChatInterface
