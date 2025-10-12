@echo off
REM Git忽略规则检查脚本 (Windows版本)
REM 用于验证.gitignore是否正确配置

echo ======================================
echo GustoBot .gitignore 检查工具
echo ======================================
echo.

REM 检查是否在Git仓库中
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 当前不在Git仓库中
    exit /b 1
)

echo ✅ Git仓库检查通过
echo.

echo 📋 检查常见忽略规则...
echo ======================================

REM 检查常见的忽略模式
call :check_pattern "node_modules/"
call :check_pattern ".idea/"
call :check_pattern "*.onnx"
call :check_pattern "*.log"
call :check_pattern ".env"
call :check_pattern "proxies.txt"
call :check_pattern "cookies.json"
call :check_pattern "data/"
call :check_pattern "*.db"
call :check_pattern "*.sqlite"

echo.
echo ======================================
echo.

echo 📊 检查已跟踪的文件...
echo ======================================

git ls-files >temp_files.txt
for /f "delims=" %%i in (temp_files.txt) do (
    if exist "%%i" (
        for %%A in ("%%i") do (
            if %%~zA gtr 1048576 (
                echo ⚠️  大文件: %%i ^(%%~zA bytes^)
            )
        )
    )
)
del temp_files.txt

echo.
echo ======================================
echo.

echo 🔒 检查敏感文件...
echo ======================================

set sensitive_found=0

git ls-files | findstr /i "\.pem$ \.key$ id_rsa$ \.env$" >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  发现敏感文件！请检查：
    git ls-files | findstr /i "\.pem$ \.key$ id_rsa$ \.env$"
    set sensitive_found=1
) else (
    echo ✅ 没有发现敏感文件
)

echo.
echo ======================================
echo.

echo 📈 被忽略的文件统计...
echo ======================================

for /f %%i in ('git status --ignored --porcelain ^| find /c "!!"') do set ignored_count=%%i
echo 被忽略的文件数: %ignored_count%

if %ignored_count% gtr 0 (
    echo.
    echo 部分被忽略的文件 ^(最多显示20个^):
    git status --ignored --porcelain | findstr "^!!" | findstr /n "^" | findstr "^[1-9]:" | findstr "^1[0-9]:" 2>nul
    git status --ignored --porcelain | findstr "^!!" | findstr /n "^" | findstr "^[2][0]:" 2>nul
)

echo.
echo ======================================
echo.

if %sensitive_found%==0 (
    echo ✅ 所有检查通过！.gitignore配置正确。
    exit /b 0
) else (
    echo ⚠️  发现一些问题，请检查上面的警告信息。
    exit /b 1
)

:check_pattern
git check-ignore -q %~1 2>nul
if errorlevel 1 (
    echo ⚠️  %~1 - 未忽略
) else (
    echo ✅ %~1 - 已忽略
)
goto :eof
