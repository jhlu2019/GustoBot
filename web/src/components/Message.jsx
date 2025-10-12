import React from 'react'
import ReactMarkdown from 'react-markdown'
import { Bot, User, Clock, Tag } from 'lucide-react'
import './Message.css'

function Message({ message }) {
  const { type, content, timestamp, metadata, error } = message

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getRouteLabel = (route) => {
    const labels = {
      knowledge: '知识库',
      chat: '闲聊',
      reject: '拒绝'
    }
    return labels[route] || route
  }

  const getRouteColor = (route) => {
    const colors = {
      knowledge: '#10b981',
      chat: '#3b82f6',
      reject: '#ef4444'
    }
    return colors[route] || '#6b7280'
  }

  return (
    <div className={`message ${type}-message ${error ? 'error-message' : ''}`}>
      <div className="message-avatar">
        {type === 'bot' ? (
          <div className="avatar bot-avatar">
            <Bot size={20} />
          </div>
        ) : (
          <div className="avatar user-avatar">
            <User size={20} />
          </div>
        )}
      </div>

      <div className="message-wrapper">
        <div className="message-header">
          <span className="message-sender">
            {type === 'bot' ? 'GustoBot' : '您'}
          </span>
          <span className="message-time">
            <Clock size={12} />
            {formatTime(timestamp)}
          </span>
        </div>

        <div className={`message-content ${error ? 'error-content' : ''}`}>
          <ReactMarkdown
            components={{
              // 自定义Markdown组件样式
              code({ node, inline, className, children, ...props }) {
                return inline ? (
                  <code className="inline-code" {...props}>
                    {children}
                  </code>
                ) : (
                  <pre className="code-block">
                    <code className={className} {...props}>
                      {children}
                    </code>
                  </pre>
                )
              },
              a({ node, children, ...props }) {
                return (
                  <a {...props} target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                )
              }
            }}
          >
            {content}
          </ReactMarkdown>
        </div>

        {metadata && (
          <div className="message-metadata">
            {metadata.route && (
              <span
                className="metadata-tag"
                style={{
                  backgroundColor: `${getRouteColor(metadata.route)}15`,
                  color: getRouteColor(metadata.route)
                }}
              >
                <Tag size={12} />
                {getRouteLabel(metadata.route)}
              </span>
            )}
            {metadata.confidence && (
              <span className="metadata-info">
                置信度: {(metadata.confidence * 100).toFixed(0)}%
              </span>
            )}
            {metadata.sources && metadata.sources.length > 0 && (
              <span className="metadata-info">
                来源: {metadata.sources.length} 个文档
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default Message
