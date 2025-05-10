@echo off
echo PowerPulse Installer for Windows
echo ===============================
echo.

:: Check for administrator privileges
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: This installer requires administrator privileges.
    echo Please right-click on this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

:: Determine Python path
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Please install Python 3.8 or newer.
    echo Visit https://www.python.org/downloads/ to download Python.
    echo.
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VERSION=%%V
echo Found Python %PYTHON_VERSION%
echo.

:: Create installation directory
set INSTALL_DIR=%ProgramFiles%\PowerPulse
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
echo Installing to %INSTALL_DIR%...
echo.

:: Copy executable or install from source
if exist "dist\PowerPulse.exe" (
    echo Installing executable...
    copy "dist\PowerPulse.exe" "%INSTALL_DIR%\PowerPulse.exe"
) else (
    echo Installing from source...
    echo Creating virtual environment...
    python -m venv "%INSTALL_DIR%\venv"
    
    echo Installing PowerPulse...
    "%INSTALL_DIR%\venv\Scripts\python.exe" -m pip install --upgrade pip
    "%INSTALL_DIR%\venv\Scripts\pip.exe" install -e .
    
    :: Create launcher script
    echo @echo off > "%INSTALL_DIR%\PowerPulse.bat"
    echo start "" "%INSTALL_DIR%\venv\Scripts\pythonw.exe" -m powerpulse --gui >> "%INSTALL_DIR%\PowerPulse.bat"
)

:: Create shortcut on desktop
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\PowerPulse.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\PowerPulse.exe'; $Shortcut.Description = 'PowerPulse Battery Monitor'; $Shortcut.Save()"

:: Create start menu entry
echo Creating Start Menu entry...
if not exist "%ProgramData%\Microsoft\Windows\Start Menu\Programs\PowerPulse" mkdir "%ProgramData%\Microsoft\Windows\Start Menu\Programs\PowerPulse"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%ProgramData%\Microsoft\Windows\Start Menu\Programs\PowerPulse\PowerPulse.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\PowerPulse.exe'; $Shortcut.Description = 'PowerPulse Battery Monitor'; $Shortcut.Save()"

:: Create uninstaller
echo Creating uninstaller...
echo @echo off > "%INSTALL_DIR%\uninstall.bat"
echo echo Uninstalling PowerPulse... >> "%INSTALL_DIR%\uninstall.bat"
echo if exist "%ProgramData%\Microsoft\Windows\Start Menu\Programs\PowerPulse" rmdir /s /q "%ProgramData%\Microsoft\Windows\Start Menu\Programs\PowerPulse" >> "%INSTALL_DIR%\uninstall.bat"
echo if exist "%USERPROFILE%\Desktop\PowerPulse.lnk" del "%USERPROFILE%\Desktop\PowerPulse.lnk" >> "%INSTALL_DIR%\uninstall.bat"
echo rmdir /s /q "%INSTALL_DIR%" >> "%INSTALL_DIR%\uninstall.bat"
echo echo PowerPulse has been uninstalled. >> "%INSTALL_DIR%\uninstall.bat"
echo pause >> "%INSTALL_DIR%\uninstall.bat"

:: Add uninstaller to Control Panel
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerPulse" /v "DisplayName" /t REG_SZ /d "PowerPulse Battery Monitor" /f
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerPulse" /v "UninstallString" /t REG_SZ /d "\"%INSTALL_DIR%\uninstall.bat\"" /f
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerPulse" /v "DisplayIcon" /t REG_SZ /d "%INSTALL_DIR%\PowerPulse.exe" /f
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerPulse" /v "Publisher" /t REG_SZ /d "Naveen Vasudevan" /f
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerPulse" /v "DisplayVersion" /t REG_SZ /d "0.1.0" /f
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerPulse" /v "NoModify" /t REG_DWORD /d 1 /f
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerPulse" /v "NoRepair" /t REG_DWORD /d 1 /f

:: Configure auto-start
echo Configuring auto-start...
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "PowerPulse" /t REG_SZ /d "\"%INSTALL_DIR%\PowerPulse.exe\" --gui" /f

echo.
echo PowerPulse has been successfully installed!
echo.
echo You can start the application from:
echo - Desktop shortcut
echo - Start Menu
echo - The application will start automatically when you log in
echo.
pause
