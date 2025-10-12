import React from 'react'
import { Lightbulb, Trash2, BarChart3 } from 'lucide-react'
import './QuickActions.css'

function QuickActions({ onQuickQuestion, onClearChat, onShowStats, disabled }) {
  const quickQuestions = [
    '怎么做红烧肉？',
    '推荐几道家常菜',
    '如何炖鸡汤？',
    '有什么快手菜推荐？'
  ]

  return (
    <div className="quick-actions">
      <div className="quick-actions-header">
        <Lightbulb size={16} />
        <span>快速开始</span>
      </div>

      <div className="quick-questions">
        {quickQuestions.map((question, index) => (
          <button
            key={index}
            className="quick-question-btn"
            onClick={() => onQuickQuestion(question)}
            disabled={disabled}
          >
            {question}
          </button>
        ))}
      </div>

      <div className="quick-tools">
        <button
          className="tool-btn"
          onClick={onShowStats}
          title="查看统计"
          disabled={disabled}
        >
          <BarChart3 size={16} />
          <span>统计</span>
        </button>
        <button
          className="tool-btn clear-btn"
          onClick={onClearChat}
          title="清空对话"
          disabled={disabled}
        >
          <Trash2 size={16} />
          <span>清空</span>
        </button>
      </div>
    </div>
  )
}

export default QuickActions
