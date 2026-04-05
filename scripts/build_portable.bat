@echo off
setlocal

if exist dist rmdir /s /q dist
if exist build\pyinstaller rmdir /s /q build\pyinstaller

py -m PyInstaller build\mahjong_switcher.spec --noconfirm --clean --distpath dist --workpath build\pyinstaller
if errorlevel 1 exit /b 1

if exist dist\MahjongSwitcher-v0.1.0-windows-x64-portable.zip del /f /q dist\MahjongSwitcher-v0.1.0-windows-x64-portable.zip
powershell -NoProfile -Command "Compress-Archive -Path 'dist\MahjongSwitcher\*' -DestinationPath 'dist\MahjongSwitcher-v0.1.0-windows-x64-portable.zip' -Force"
if errorlevel 1 exit /b 1

echo Build completed.
endlocal
