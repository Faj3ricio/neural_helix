#!/bin/bash

# Configuração do layout de teclado
setxkbmap br

# Atualização de pacotes e instalação de pacotes necessários
sudo apt update -y
sudo apt install -y pipx
sudo apt install -y python3-poetry
sudo apt-get install -y python3-tk
sudo apt install -y wine
sudo apt install -y xdotool
sudo apt install -y unixodbc unixodbc-dev
sudo apt install -y odbcinst msodbcsql17

# Adicionando repositórios Microsoft
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

# Atualizando e instalando o driver MS ODBC
sudo apt update -y
sudo ACCEPT_EULA=Y apt install -y msodbcsql17

# Instalando o Google Chrome
sudo wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb

# Caso haja dependências faltando após o dpkg
sudo apt --fix-broken install -y

echo "Configuração concluída!"