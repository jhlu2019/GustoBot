import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  RiMessage3Fill,
  RiCloseLine,
  RiSendPlaneFill,
  RiAttachmentLine,
  RiImageLine,
  RiExpandDiagonalLine,
  AiFillRobot,
  AiOutlineLoading3Quarters
} from '@remixicon/react';
import ChatService from '../services/ChatService';
import MessageBubble from './MessageBubble';

const ChatWidget = ({ fullscreen = false }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [routeInfo, setRouteInfo] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // 初始化会话
    const savedSessionId = localStorage.getItem('gustobot_session_id');
    if (savedSessionId) {
      setSessionId(savedSessionId);
    }

    // 添加欢迎消息
    if (!fullscreen && messages.length === 0) {
      setMessages([{
        type: 'assistant',
        content: '您好！我是GustoBot 👋\n可以帮您查询菜谱、了解历史、统计数据等',
        route: 'general-query'
      }]);
    }
  }, [fullscreen, messages.length]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setInputValue('');

    try {
      const response = await ChatService.sendMessage({
        message: inputValue,
        session_id: sessionId,
        user_id: fullscreen ? 'web_fullscreen' : 'web_widget'
      });

      if (response.session_id) {
        setSessionId(response.session_id);
        localStorage.setItem('gustobot_session_id', response.session_id);
      }

      const assistantMessage = {
        type: 'assistant',
        content: response.message,
        route: response.route,
        sources: response.sources,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setRouteInfo(response.route);

      // 3秒后隐藏路由信息
      setTimeout(() => setRouteInfo(null), 3000);
    } catch (error) {
      console.error('发送消息失败:', error);
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: '抱歉，发送消息失败，请稍后重试。',
        route: 'error'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

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

  if (fullscreen) {
    return (
      <div className="h-[600px] flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.map((msg, index) => (
            <MessageBubble key={index} message={msg} />
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-gray-200 p-4 bg-white">
          {routeInfo && (
            <div className="mb-2">
              <span className="route-badge">
                路由: {getRouteDisplayName(routeInfo)}
              </span>
            </div>
          )}

          <div className="flex items-center gap-2">
            <button className="p-2 text-gray-500 hover:text-purple-600 transition">
              <RiAttachmentLine size={20} />
            </button>
            <button className="p-2 text-gray-500 hover:text-purple-600 transition">
              <RiImageLine size={20} />
            </button>
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="问我任何关于菜谱的问题..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !inputValue.trim()}
              className="px-4 py-2 bg-purple-600 text-white rounded-full hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <AiOutlineLoading3Quarters className="animate-spin" size={16} />
              ) : (
                <RiSendPlaneFill size={16} />
              )}
              <span>发送</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {!isOpen && (
        <motion.button
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setIsOpen(true)}
          className="w-14 h-14 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all flex items-center justify-center"
        >
          <RiMessage3Fill size={24} />
        </motion.button>
      )}

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mb-4 w-80 h-96 bg-white rounded-2xl shadow-xl flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AiFillRobot size={20} />
                <span className="font-semibold">GustoBot</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => window.open('/fullscreen', '_blank')}
                  className="hover:bg-white/20 rounded p-1 transition"
                >
                  <RiExpandDiagonalLine size={16} />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="hover:bg-white/20 rounded p-1 transition"
                >
                  <RiCloseLine size={16} />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2 bg-gray-50">
              {messages.map((msg, index) => (
                <MessageBubble key={index} message={msg} compact />
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-3 border-t border-gray-200 bg-white">
              <div className="flex items-center gap-1">
                <button className="p-1.5 text-gray-500 hover:text-purple-600 transition">
                  <RiAttachmentLine size={18} />
                </button>
                <button className="p-1.5 text-gray-500 hover:text-purple-600 transition">
                  <RiImageLine size={18} />
                </button>
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="输入消息..."
                  className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500"
                  disabled={isLoading}
                />
                <button
                  onClick={handleSend}
                  disabled={isLoading || !inputValue.trim()}
                  className="p-1.5 bg-purple-600 text-white rounded-full hover:bg-purple-700 transition disabled:opacity-50"
                >
                  {isLoading ? (
                    <AiOutlineLoading3Quarters className="animate-spin" size={14} />
                  ) : (
                    <RiSendPlaneFill size={14} />
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ChatWidget;