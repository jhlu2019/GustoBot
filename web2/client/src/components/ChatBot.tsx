import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessageCircle, Send, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  text: string;
  sender: "user" | "bot";
  timestamp: Date;
}

export default function ChatBot() {
  const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: "你好！我是菜谱助手。有什么菜谱问题我可以帮助你吗？",
      sender: "bot",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    // Simulate bot response
    setTimeout(() => {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: generateBotResponse(inputValue),
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
      setIsLoading(false);
    }, 800);
  };

  const generateBotResponse = (userInput: string): string => {
    const responses: { [key: string]: string } = {
      菜谱: "我们有很多美味的菜谱！您可以浏览我们的菜谱列表，或告诉我您想要什么类型的菜。",
      推荐:
        "根据季节，我推荐您试试番茄鸡蛋汤、清蒸鱼或红烧肉。您对哪一个感兴趣？",
      简单: "简单的菜谱有：炒青菜、番茄鸡蛋、清汤面。这些都很容易做！",
      难度: "我们的菜谱从初级到高级都有。您想要简单快手菜还是复杂的大餐？",
      时间: "快手菜通常需要15-30分钟，而复杂菜肴可能需要1-2小时。",
      材料: "告诉我您有什么材料，我可以推荐相应的菜谱给您！",
    };

    for (const [keyword, response] of Object.entries(responses)) {
      if (userInput.includes(keyword)) {
        return response;
      }
    }

    return "这是一个很好的问题！您可以告诉我更多关于您想要的菜谱类型吗？比如：简单快手菜、家常菜或特色菜？";
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Chat Window */}
      {isOpen && (
        <div className="absolute bottom-20 right-0 w-96 h-96 bg-white rounded-lg shadow-2xl flex flex-col border border-gray-200">
          {/* Header */}
          <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-4 rounded-t-lg flex justify-between items-center">
            <div className="flex items-center gap-2">
              <MessageCircle size={20} />
              <span className="font-semibold">菜谱助手</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(false)}
              className="text-white hover:bg-white/20"
            >
              <X size={18} />
            </Button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex",
                  message.sender === "user" ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={cn(
                    "max-w-xs px-4 py-2 rounded-lg",
                    message.sender === "user"
                      ? "bg-orange-500 text-white rounded-br-none"
                      : "bg-white text-gray-800 border border-gray-200 rounded-bl-none"
                  )}
                >
                  <p className="text-sm">{message.text}</p>
                  <span className="text-xs opacity-70 mt-1 block">
                    {message.timestamp.toLocaleTimeString("zh-CN", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white text-gray-800 border border-gray-200 px-4 py-2 rounded-lg rounded-bl-none">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 p-4 bg-white rounded-b-lg flex gap-2">
            <Input
              type="text"
              placeholder="输入您的问题..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  handleSendMessage();
                }
              }}
              disabled={isLoading}
              className="flex-1"
            />
            <Button
              onClick={handleSendMessage}
              disabled={isLoading || !inputValue.trim()}
              className="bg-orange-500 hover:bg-orange-600 text-white"
              size="sm"
            >
              <Send size={18} />
            </Button>
          </div>
        </div>
      )}

      {/* Toggle Button */}
      <Button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "rounded-full w-14 h-14 shadow-lg",
          isOpen
            ? "bg-red-500 hover:bg-red-600"
            : "bg-orange-500 hover:bg-orange-600"
        )}
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </Button>
    </div>
  );
}
