import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Search, Clock, Users } from "lucide-react";

interface Recipe {
  id: number;
  title: string;
  description: string;
  image: string;
  time: string;
  servings: string;
  difficulty: "简单" | "中等" | "困难";
  ingredients: string[];
  steps: string[];
}

const recipes: Recipe[] = [
  {
    id: 1,
    title: "番茄鸡蛋汤",
    description: "清汤爽口，营养丰富的家常汤品",
    image: "https://images.unsplash.com/photo-1547592166-7aae4d755744?w=400&h=300&fit=crop",
    time: "15分钟",
    servings: "4人份",
    difficulty: "简单",
    ingredients: ["番茄2个", "鸡蛋2个", "清汤600ml", "盐适量", "油适量"],
    steps: [
      "番茄切块，鸡蛋打散",
      "热油爆香番茄",
      "加入清汤烧开",
      "倒入蛋花，煮至凝固",
      "调味即可"
    ]
  },
  {
    id: 2,
    title: "清蒸鱼",
    description: "鲜嫩多汁，清淡健康的经典菜肴",
    image: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop",
    time: "20分钟",
    servings: "3人份",
    difficulty: "简单",
    ingredients: ["鲜鱼1条", "姜丝适量", "葱段适量", "酱油2汤匙", "油1汤匙"],
    steps: [
      "鱼洗净，放入蒸盘",
      "铺上姜丝和葱段",
      "大火蒸12-15分钟",
      "淋上酱油和热油",
      "撒上葱花即可"
    ]
  },
  {
    id: 3,
    title: "红烧肉",
    description: "肥而不腻，色泽诱人的传统名菜",
    image: "https://images.unsplash.com/photo-1432139555190-58524dae6a55?w=400&h=300&fit=crop",
    time: "90分钟",
    servings: "6人份",
    difficulty: "中等",
    ingredients: ["猪五花肉800g", "冰糖50g", "酱油3汤匙", "姜片适量", "葱段适量"],
    steps: [
      "猪肉切块，焯水",
      "炒冰糖至焦糖色",
      "放入猪肉翻炒",
      "加入酱油、姜、葱和清水",
      "炖煮60分钟至软烂"
    ]
  },
  {
    id: 4,
    title: "炒青菜",
    description: "快手菜，保留蔬菜的鲜绿色泽",
    image: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop",
    time: "10分钟",
    servings: "2人份",
    difficulty: "简单",
    ingredients: ["青菜500g", "蒜瓣3个", "油2汤匙", "盐适量", "鸡精适量"],
    steps: [
      "青菜洗净，沥干",
      "蒜瓣切碎",
      "热油爆香蒜",
      "放入青菜快速炒",
      "调味即可出锅"
    ]
  },
  {
    id: 5,
    title: "宫保鸡丁",
    description: "酸辣开胃，经典川菜代表",
    image: "https://images.unsplash.com/photo-1585521537066-a3b4a4a37d2a?w=400&h=300&fit=crop",
    time: "25分钟",
    servings: "4人份",
    difficulty: "中等",
    ingredients: ["鸡胸肉300g", "花生米100g", "干辣椒5个", "酱油2汤匙", "醋1汤匙"],
    steps: [
      "鸡肉切丁，腌制",
      "炒花生米至香",
      "炒鸡丁至半熟",
      "加入辣椒和酱油",
      "加入花生米翻炒均匀"
    ]
  },
  {
    id: 6,
    title: "番茄意粉",
    description: "西餐风味，简单快手的意大利面",
    image: "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=400&h=300&fit=crop",
    time: "20分钟",
    servings: "2人份",
    difficulty: "简单",
    ingredients: ["意粉200g", "番茄罐头1罐", "洋葱1个", "蒜瓣2个", "橄榄油适量"],
    steps: [
      "意粉煮至弹牙",
      "洋葱蒜切碎炒香",
      "加入番茄罐头炖煮",
      "沥干意粉加入酱汁",
      "拌匀即可享用"
    ]
  }
];

export default function Home() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [difficultyFilter, setDifficultyFilter] = useState<string>("全部");

  const filteredRecipes = recipes.filter((recipe) => {
    const matchesSearch = recipe.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      recipe.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDifficulty = difficultyFilter === "全部" || recipe.difficulty === difficultyFilter;
    return matchesSearch && matchesDifficulty;
  });

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 to-white">
      {/* Search and Filter */}
      <div className="bg-white border-b border-gray-200 sticky top-16 z-40">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex flex-col gap-4">
            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-3 top-3 text-gray-400" size={20} />
              <Input
                type="text"
                placeholder="搜索菜谱..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 py-2 rounded-lg border border-gray-300"
              />
            </div>

            {/* Difficulty Filter */}
            <div className="flex gap-2 flex-wrap">
              {["全部", "简单", "中等", "困难"].map((difficulty) => (
                <Button
                  key={difficulty}
                  onClick={() => setDifficultyFilter(difficulty)}
                  variant={difficultyFilter === difficulty ? "default" : "outline"}
                  className={difficultyFilter === difficulty ? "bg-orange-500 hover:bg-orange-600" : ""}
                >
                  {difficulty}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-12">
        {selectedRecipe ? (
          // Recipe Detail View
          <div className="bg-white rounded-lg shadow-lg p-8">
            <Button
              onClick={() => setSelectedRecipe(null)}
              variant="outline"
              className="mb-6"
            >
              ← 返回列表
            </Button>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Recipe Image */}
              <div>
                <img
                  src={selectedRecipe.image}
                  alt={selectedRecipe.title}
                  className="w-full h-96 object-cover rounded-lg"
                />
              </div>

              {/* Recipe Info */}
              <div>
                <h1 className="text-4xl font-bold mb-4">{selectedRecipe.title}</h1>
                <p className="text-gray-600 text-lg mb-6">{selectedRecipe.description}</p>

                {/* Meta Info */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                  <div className="flex items-center gap-2">
                    <Clock size={20} className="text-orange-500" />
                    <div>
                      <p className="text-sm text-gray-500">烹饪时间</p>
                      <p className="font-semibold">{selectedRecipe.time}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users size={20} className="text-orange-500" />
                    <div>
                      <p className="text-sm text-gray-500">份量</p>
                      <p className="font-semibold">{selectedRecipe.servings}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">难度</p>
                    <p className={`font-semibold ${
                      selectedRecipe.difficulty === "简单" ? "text-green-600" :
                      selectedRecipe.difficulty === "中等" ? "text-yellow-600" :
                      "text-red-600"
                    }`}>
                      {selectedRecipe.difficulty}
                    </p>
                  </div>
                </div>

                {/* Ingredients */}
                <div className="mb-8">
                  <h2 className="text-2xl font-bold mb-4">材料</h2>
                  <ul className="space-y-2">
                    {selectedRecipe.ingredients.map((ingredient, index) => (
                      <li key={index} className="flex items-center gap-2">
                        <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                        {ingredient}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Steps */}
                <div>
                  <h2 className="text-2xl font-bold mb-4">做法</h2>
                  <ol className="space-y-3">
                    {selectedRecipe.steps.map((step, index) => (
                      <li key={index} className="flex gap-4">
                        <span className="flex-shrink-0 w-8 h-8 bg-orange-500 text-white rounded-full flex items-center justify-center font-bold">
                          {index + 1}
                        </span>
                        <span className="pt-1">{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // Recipe Grid View
          <>
            <h2 className="text-3xl font-bold mb-8">
              {filteredRecipes.length > 0
                ? `找到 ${filteredRecipes.length} 个菜谱`
                : "没有找到符合条件的菜谱"}
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredRecipes.map((recipe) => (
                <Card
                  key={recipe.id}
                  className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => setSelectedRecipe(recipe)}
                >
                  <div className="relative overflow-hidden h-48">
                    <img
                      src={recipe.image}
                      alt={recipe.title}
                      className="w-full h-full object-cover hover:scale-105 transition-transform"
                    />
                    <div className="absolute top-2 right-2 bg-orange-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                      {recipe.difficulty}
                    </div>
                  </div>

                  <CardHeader>
                    <CardTitle className="text-xl">{recipe.title}</CardTitle>
                    <CardDescription>{recipe.description}</CardDescription>
                  </CardHeader>

                  <CardContent>
                    <div className="flex justify-between text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <Clock size={16} />
                        {recipe.time}
                      </div>
                      <div className="flex items-center gap-1">
                        <Users size={16} />
                        {recipe.servings}
                      </div>
                    </div>
                    <Button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedRecipe(recipe);
                      }}
                      className="w-full mt-4 bg-orange-500 hover:bg-orange-600"
                    >
                      查看详情
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 mt-16">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p>© 2024 菜谱网站。享受烹饪，分享美食。</p>
        </div>
      </footer>
    </div>
  );
}
