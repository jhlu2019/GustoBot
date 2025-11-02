import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useLocation } from "wouter";
import { APP_LOGO, APP_TITLE } from "@/const";
import { LogOut } from "lucide-react";

export default function Header() {
  const [, setLocation] = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const loggedIn = localStorage.getItem("isLoggedIn") === "true";
    const email = localStorage.getItem("userEmail") || "";
    setIsLoggedIn(loggedIn);
    setUserEmail(email);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("isLoggedIn");
    localStorage.removeItem("userEmail");
    setIsLoggedIn(false);
    setLocation("/");
  };

  const handleLogin = () => {
    setLocation("/login");
  };

  return (
    <header className="bg-gradient-to-r from-orange-500 to-red-500 text-white py-4 px-4 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div
          className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
          onClick={() => setLocation("/")}
        >
          {APP_LOGO && <img src={APP_LOGO} alt="logo" className="w-10 h-10" />}
          <h1 className="text-2xl font-bold">{APP_TITLE || "菜谱网站"}</h1>
        </div>

        <div className="flex items-center gap-4">
          {isLoggedIn ? (
            <>
              <span className="text-sm opacity-90">欢迎，{userEmail}</span>
              <Button
                onClick={handleLogout}
                variant="ghost"
                className="text-white hover:bg-white/20 flex items-center gap-2"
              >
                <LogOut size={18} />
                退出登录
              </Button>
            </>
          ) : (
            <Button
              onClick={handleLogin}
              className="bg-white text-orange-500 hover:bg-gray-100 font-semibold"
            >
              登录
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
