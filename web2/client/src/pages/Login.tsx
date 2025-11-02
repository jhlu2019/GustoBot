import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useLocation } from "wouter";
import { APP_LOGO, APP_TITLE } from "@/const";

export default function Login() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    // 模拟登录请求
    setTimeout(() => {
      // 存储登录状态
      localStorage.setItem("isLoggedIn", "true");
      localStorage.setItem("userEmail", email);
      setIsLoading(false);
      // 重定向到首页
      setLocation("/");
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 to-white flex items-center justify-center px-4">
      <Card className="w-full max-w-md" style={{backgroundColor: '#ffffff'}}>
        <CardHeader className="text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            {APP_LOGO && <img src={APP_LOGO} alt="logo" className="w-8 h-8" />}
            <h1 className="text-2xl font-bold">{APP_TITLE || "菜谱网站"}</h1>
          </div>
          <CardTitle>登录账户</CardTitle>
          <CardDescription>输入您的邮箱和密码登录</CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">邮箱</label>
              <Input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">密码</label>
              <Input
                type="password"
                placeholder="输入您的密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-orange-500 hover:bg-orange-600"
            >
              {isLoading ? "登录中..." : "登录"}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            <p>还没有账户？<a href="#" className="text-orange-500 hover:text-orange-600 font-semibold">立即注册</a></p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
