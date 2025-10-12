#!/bin/bash
# Git忽略规则检查脚本
# 用于验证.gitignore是否正确配置

echo "======================================"
echo "GustoBot .gitignore 检查工具"
echo "======================================"
echo ""

# 检查是否在Git仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ 错误: 当前不在Git仓库中"
    exit 1
fi

echo "✅ Git仓库检查通过"
echo ""

# 定义需要检查的模式
declare -a patterns=(
    "node_modules/"
    ".idea/"
    "*.onnx"
    "*.log"
    ".env"
    "proxies.txt"
    "cookies.json"
    "data/"
    "*.db"
    "*.sqlite"
)

echo "📋 检查常见忽略规则..."
echo "======================================"

all_passed=true

for pattern in "${patterns[@]}"; do
    # 检查模式是否在.gitignore中
    if git check-ignore -q "$pattern" 2>/dev/null; then
        echo "✅ $pattern - 已忽略"
    else
        echo "⚠️  $pattern - 未忽略"
        all_passed=false
    fi
done

echo ""
echo "======================================"

# 检查是否有大文件被跟踪
echo ""
echo "📊 检查已跟踪的大文件（>1MB）..."
echo "======================================"

large_files=$(git ls-files | xargs -I {} du -h {} 2>/dev/null | awk '$1 ~ /M$|G$/ {print $2, $1}' | sort -hr)

if [ -z "$large_files" ]; then
    echo "✅ 没有发现大于1MB的已跟踪文件"
else
    echo "⚠️  发现以下大文件:"
    echo "$large_files"
    all_passed=false
fi

echo ""
echo "======================================"

# 检查是否有敏感文件
echo ""
echo "🔒 检查敏感文件..."
echo "======================================"

declare -a sensitive_patterns=(
    "*.pem"
    "*.key"
    "id_rsa"
    ".env"
    "secrets/"
)

sensitive_found=false

for pattern in "${sensitive_patterns[@]}"; do
    files=$(git ls-files | grep -E "$pattern" 2>/dev/null)
    if [ ! -z "$files" ]; then
        echo "⚠️  发现敏感文件: $files"
        sensitive_found=true
        all_passed=false
    fi
done

if [ "$sensitive_found" = false ]; then
    echo "✅ 没有发现敏感文件"
fi

echo ""
echo "======================================"

# 显示被忽略的文件统计
echo ""
echo "📈 被忽略的文件统计..."
echo "======================================"

ignored_count=$(git status --ignored --porcelain | grep "^!!" | wc -l)
echo "被忽略的文件数: $ignored_count"

if [ $ignored_count -gt 0 ]; then
    echo ""
    echo "部分被忽略的文件（最多显示20个）:"
    git status --ignored --porcelain | grep "^!!" | head -20 | sed 's/^!! /  - /'
fi

echo ""
echo "======================================"

# 最终结果
echo ""
if [ "$all_passed" = true ]; then
    echo "✅ 所有检查通过！.gitignore配置正确。"
    exit 0
else
    echo "⚠️  发现一些问题，请检查上面的警告信息。"
    exit 1
fi
