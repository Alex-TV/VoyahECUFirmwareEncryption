@echo off
cd /d "D:\Projects\Python\VoyahECUFirmwareEncryption"

echo === Building Voyah ECU Tool ===

pyinstaller --noconfirm ^
  --onefile ^
  --windowed ^
  --name "VoyahECUTool" ^
  --icon "resources/icons/favicon.ico" ^
  --hidden-import "PyQt5" ^
  --hidden-import "PyQt5.QtCore" ^
  --hidden-import "PyQt5.QtGui" ^
  --hidden-import "PyQt5.QtWidgets" ^
  --add-data "resources;resources" ^
  "main.py"

echo === Copying files to EXE directory ===

:: Создаем целевую папку если не существует
if not exist "dist\resources\ca" mkdir "dist\resources\ca"

:: Копируем настройки
if exist "setting.ini" (
    copy "setting.ini" "dist\"
    echo ✅ setting.ini copied
) else (
    echo ⚠️ setting.ini not found
)

:: Копируем README
if exist "README.md" (
    copy "README.md" "dist\"
    echo ✅ README.md copied
)

:: Копируем CA сертификаты
if exist "resources\ca" (
    xcopy "resources\ca" "dist\resources\ca" /E /I /Y /Q
    echo ✅ CA certificates copied
) else (
    echo ⚠️ resources\ca folder not found
)

echo.
echo ✅ Build complete!
echo 📁 EXE location: dist\VoyahECUTool.exe
echo 📄 Settings: dist\setting.ini
echo 🔐 CA certs: dist\resources\ca\
echo.
echo 📋 Final structure:
dir "dist\" /B
echo.
dir "dist\resources" /B
pause