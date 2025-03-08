@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 设置代码页为UTF-8
for /f "tokens=2 delims=:" %%a in ('chcp') do set "_OLD_CODEPAGE=%%a"
chcp 65001 >nul

echo ===================================
echo 启动前检查必要运行库...
echo ===================================

:: 设置错误处理
set "ERROR_VC_MISSING=1"
set "ERROR_PYMUPDF_MISSING=2"
set "ERROR_NETWORK=3"
set "ERROR_APP_MISSING=4"

:: 检查chaifenup.exe是否存在
if not exist "%~dp0dist\chaifenup.exe" (
    echo 错误: 未找到应用程序文件 chaifenup.exe
    echo 请确保已正确打包应用程序
    pause
    exit /b %ERROR_APP_MISSING%
)

:: 检查VC++运行库
echo 检查 Visual C++ 运行库...
set "vcredist_missing=0"

:: 检查常见VC++运行库DLL
set "system32=%windir%\System32"

:: 检查VC++ 2015-2022运行库
if not exist "%system32%\vcruntime140.dll" set "vcredist_missing=1"
if not exist "%system32%\msvcp140.dll" set "vcredist_missing=1"

if %vcredist_missing% equ 1 (
    echo 警告: 未找到必要的Visual C++运行库
    echo 应用程序可能无法正常运行
    echo 建议安装最新的Visual C++ Redistributable
    choice /C YN /M "是否继续启动应用程序"
    if errorlevel 2 exit /b %ERROR_VC_MISSING%
) else (
    echo Visual C++运行库检查通过
)

:: 检查PyMuPDF相关DLL
echo 检查PyMuPDF相关组件...
set "app_dir=%~dp0dist"
set "pymupdf_missing=0"

:: 检查常见的MuPDF相关文件
if not exist "%app_dir%\fitz\_fitz.pyd" set "pymupdf_missing=1"

if %pymupdf_missing% equ 1 (
    echo 警告: 未找到PyMuPDF相关组件
    echo PDF处理功能可能无法正常工作
    choice /C YN /M "是否继续启动应用程序"
    if errorlevel 2 exit /b %ERROR_PYMUPDF_MISSING%
) else (
    echo PyMuPDF组件检查通过
)

:: 检查网络连接
echo 检查网络连接...
ping -n 1 api.siliconflow.cn >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告: 无法连接到AI API服务器(api.siliconflow.cn)
    echo AI功能可能无法正常工作
    echo 请检查您的网络连接
    choice /C YN /M "是否继续启动应用程序"
    if errorlevel 2 exit /b %ERROR_NETWORK%
) else (
    echo 网络连接检查通过
)

echo ===================================
echo 所有检查完成，正在启动应用程序...
echo ===================================

:: 启动应用程序
start "" "%~dp0dist\chaifenup.exe"

endlocal
exit /b 0