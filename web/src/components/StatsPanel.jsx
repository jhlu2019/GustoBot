import React, { useEffect, useState } from 'react'
import { X, Database, MessageSquare, TrendingUp, Layers } from 'lucide-react'
import { getKnowledgeStats } from '../services/api'
import './StatsPanel.css'

function StatsPanel({ isOpen, onClose }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (isOpen) {
      fetchStats()
    }
  }, [isOpen])

  const fetchStats = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getKnowledgeStats()
      setStats(data)
    } catch (err) {
      console.error('Failed to fetch stats:', err)
      setError('获取统计信息失败')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="stats-panel-overlay" onClick={onClose}>
      <div className="stats-panel" onClick={(e) => e.stopPropagation()}>
        <div className="stats-panel-header">
          <h3>系统统计</h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="stats-panel-content">
          {loading ? (
            <div className="stats-loading">
              <div className="spinner"></div>
              <p>加载中...</p>
            </div>
          ) : error ? (
            <div className="stats-error">
              <p>{error}</p>
              <button className="retry-btn" onClick={fetchStats}>
                重试
              </button>
            </div>
          ) : stats ? (
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon" style={{ background: '#dbeafe' }}>
                  <Database size={24} color="#3b82f6" />
                </div>
                <div className="stat-content">
                  <div className="stat-value">{stats.total_documents || 0}</div>
                  <div className="stat-label">文档总数</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon" style={{ background: '#d1fae5' }}>
                  <MessageSquare size={24} color="#10b981" />
                </div>
                <div className="stat-content">
                  <div className="stat-value">{stats.total_recipes || 0}</div>
                  <div className="stat-label">菜谱数量</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon" style={{ background: '#fef3c7' }}>
                  <TrendingUp size={24} color="#f59e0b" />
                </div>
                <div className="stat-content">
                  <div className="stat-value">
                    {stats.embedding_dimension || 1536}
                  </div>
                  <div className="stat-label">向量维度</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon" style={{ background: '#e9d5ff' }}>
                  <Layers size={24} color="#a855f7" />
                </div>
                <div className="stat-content">
                  <div className="stat-value">
                    {stats.embedding_model || 'text-embedding-3-small'}
                  </div>
                  <div className="stat-label">嵌入模型</div>
                </div>
              </div>

              {stats.reranker_model && (
                <div className="stat-card full-width">
                  <div className="stat-info">
                    <strong>Reranker:</strong>
                    <span>{stats.reranker_model.provider || 'N/A'}</span>
                  </div>
                  <div className="stat-info">
                    <strong>状态:</strong>
                    <span className={stats.reranker_model.available ? 'status-active' : 'status-inactive'}>
                      {stats.reranker_model.available ? '可用' : '不可用'}
                    </span>
                  </div>
                </div>
              )}

              {stats.collection_name && (
                <div className="stat-card full-width">
                  <div className="stat-info">
                    <strong>向量集合:</strong>
                    <span>{stats.collection_name}</span>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>

        <div className="stats-panel-footer">
          <button className="refresh-btn" onClick={fetchStats} disabled={loading}>
            刷新数据
          </button>
        </div>
      </div>
    </div>
  )
}

export default StatsPanel
