import React from 'react';
import { motion } from 'framer-motion';

const MessageBubble = ({ message, compact = false }) => {
  const isUser = message.type === 'user';
  const bubbleClass = isUser ? 'chat-bubble user' : 'chat-bubble assistant';
  const containerClass = isUser ? 'justify-end' : 'justify-start';

  const getRouteDisplayName = (route) => {
    const routeNames = {
      'general-query': '日常对话',
      'additional-query': '补充信息',
      'kb-query': '知识库查询',
      'graphrag-query': '图谱查询',
      'text2sql-query': '统计查询',
      'image-query': '图片处理',
      'file-query': '文件处理'
    };
    return routeNames[route] || route;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${containerClass} ${compact ? 'mb-2' : 'mb-4'}`}
    >
      <div className={`${bubbleClass} ${compact ? 'text-sm' : ''}`}>
        <div className="whitespace-pre-wrap">{message.content}</div>

        {!isUser && message.route && (
          <div className={`${compact ? 'text-xs' : 'text-sm'} text-gray-500 mt-1`}>
            <i className="ri-route-line"></i> {getRouteDisplayName(message.route)}
          </div>
        )}

        {message.sources && message.sources.length > 0 && !compact && (
          <div className="mt-2 space-y-1">
            {message.sources.slice(0, 2).map((source, idx) => (
              <div key={idx} className="source-item">
                <i className="ri-bookmark-line"></i> {source.title || '来源'}
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default MessageBubble;