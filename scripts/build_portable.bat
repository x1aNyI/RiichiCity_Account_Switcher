@echo off
setlocal

set "VERSION=%~1"
if not defined VERSION set "VERSION=v0.1.0"
set "ZIP_NAME=MahjongSwitcher-%VERSION%-windows-x64-portable.zip"
set "ZIP_PATH=dist\%ZIP_NAME%"

if exist dist rmdir /s /q dist
if exist build\pyinstaller rmdir /s /q build\pyinstaller

python -m PyInstaller build\mahjong_switcher.spec --noconfirm --clean --distpath dist --workpath build\pyinstaller
if errorlevel 1 exit /b 1

if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\MahjongSwitcher\*' -DestinationPath '%ZIP_PATH%' -Force"
if errorlevel 1 exit /b 1

echo Build completed: %ZIP_NAME%
endlocal
