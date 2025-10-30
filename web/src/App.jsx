import React, { useState, useEffect } from 'react';
import ChatWidget from './components/ChatWidget';
import { motion } from 'framer-motion';

function App() {
  const [showWelcome, setShowWelcome] = useState(true);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
      {showWelcome ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="min-h-screen flex items-center justify-center"
        >
          <div className="text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring" }}
              className="mb-8"
            >
              <div className="text-8xl">🍳</div>
            </motion.div>
            <motion.h1
              initial={{ y: -50 }}
              animate={{ y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-4xl font-bold text-gray-800 mb-2"
            >
              GustoBot
            </motion.h1>
            <motion.p
              initial={{ y: 50 }}
              animate={{ y: 0 }}
              transition={{ delay: 0.4 }}
              className="text-xl text-gray-600 mb-8"
            >
              智能菜谱助手
            </motion.p>
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              onClick={() => setShowWelcome(false)}
              className="px-8 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-full hover:from-purple-700 hover:to-indigo-700 transition transform hover:scale-105"
            >
              开始对话
            </motion.button>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="text-gray-500 text-sm mt-4"
            >
              或使用右下角的聊天小部件
            </motion.p>
          </div>
        </motion.div>
      ) : (
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="w-full max-w-4xl">
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
              <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-6 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-3xl">🍳</div>
                  <div>
                    <h1 className="text-2xl font-bold">GustoBot</h1>
                    <p className="text-purple-100 text-sm">智能菜谱助手</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowWelcome(true)}
                  className="text-white hover:text-purple-200 transition"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="h-[600px]">
                <ChatWidget fullscreen={true} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 聊天小部件始终显示 */}
      <ChatWidget />
    </div>
  );
}

export default App;