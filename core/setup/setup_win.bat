# Script para configurar ambiente Windows

# Forçar o uso de TLS 1.2
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

# Verifica se o script está sendo executado como administrador e no Power Shell
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Execute este script como Administrador!" -ForegroundColor Red
    exit
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git não está instalado. Baixando e instalando Git..." -ForegroundColor Green
    Invoke-WebRequest -Uri "https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.1/Git-2.42.0-64-bit.exe" -OutFile "git-installer.exe"
    Start-Process -FilePath "git-installer.exe" -ArgumentList "/silent" -Wait
    Remove-Item "git-installer.exe"
    Write-Host "Git instalado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "Git já está instalado." -ForegroundColor Yellow
}

# Instalação do Python (se não estiver instalado)
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python não encontrado. Baixando e instalando Python..." -ForegroundColor Green
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe" -OutFile "python-installer.exe"
    Start-Process -FilePath "python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
    Remove-Item "python-installer.exe"
    Write-Host "Python instalado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "Python já está instalado." -ForegroundColor Yellow
}

# Instalação do pipx
Write-Host "Instalando pipx..." -ForegroundColor Green
python -m pip install --user pipx
python -m pipx ensurepath

# Instalação do Poetry
Write-Host "Instalando Poetry..." -ForegroundColor Green
pipx install poetry

# Instalação do Python TK
Write-Host "Instalando suporte a Python TK (opcional)..." -ForegroundColor Green
python -m pip install tk

# Instalação do Google Chrome
if (-not (Get-Command "chrome.exe" -ErrorAction SilentlyContinue)) {
    Write-Host "Baixando e instalando o Google Chrome..." -ForegroundColor Green
    Invoke-WebRequest -Uri "https://dl.google.com/chrome/install/latest/chrome_installer.exe" -OutFile "chrome_installer.exe"
    Start-Process -FilePath "chrome_installer.exe" -ArgumentList "/silent /install" -Wait
    Remove-Item "chrome_installer.exe"
    Write-Host "Google Chrome instalado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "Google Chrome já está instalado." -ForegroundColor Yellow
}

# Instalação do Microsoft ODBC Driver (SQL Server)
Write-Host "Instalando driver ODBC para SQL Server..." -ForegroundColor Green
Invoke-WebRequest -Uri "https://go.microsoft.com/fwlink/?linkid=2166101" -OutFile "msodbcsql.msi"
Start-Process -FilePath "msodbcsql.msi" -ArgumentList "/quiet" -Wait
Remove-Item "msodbcsql.msi"
Write-Host "Driver ODBC instalado com sucesso!" -ForegroundColor Green

# Criação da pasta "repos" e entrada nela
Write-Host "Criando pasta 'repos'..." -ForegroundColor Green
New-Item -ItemType Directory -Path "$HOME\repos" -Force | Out-Null
Set-Location "$HOME\repos"
Write-Host "Pasta 'repos' criada e acessada com sucesso!" -ForegroundColor Green

Write-Host "Configuração concluída com sucesso!" -ForegroundColor Green