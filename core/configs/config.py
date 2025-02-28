# config.py
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import os


# Caminho absoluto do .env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "credentials", ".env"))
# Carrega o .env
load_dotenv(dotenv_path)

# Diretório de download configurado
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'neural_dataflow', 'data', 'raw')
ChromeOptions = Options
def chromeBrowserOptions():
    options = ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument(f"--profile-directory={profile_name}")  # Define o perfil específico
    options.add_argument("--disable-blink-features=AutomationControlled")  # Evita detecção automática
    DOWNLOAD_DIR = os.path.abspath(
        os.path.join(os.getcwd().split('neural_dataflow')[0], 'neural_dataflow', 'data', 'raw'))
    # Diretório de download
    options.add_argument("--start-maximized")
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,  # Diretório de download
        "download.prompt_for_download": False,  # Baixar sem prompt
        "download.directory_upgrade": True,  # Permitir substituir o diretório
        "safebrowsing.enabled": True,  # Desativa verificação de downloads perigosos
        "profile.default_content_setting_values.automatic_downloads": 1,  # Permitir múltiplos downloads
        "profile.password_manager_enabled": False,
        "credentials_enable_service": False,
        "webrtc.ip_handling_policy": "disable_non_proxied_udp"
    }
    options.add_experimental_option("prefs", prefs)  # Configurações adicionais
    options.add_argument('--no-sandbox')
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-password-manager-reauthentication")
    options.add_experimental_option("prefs", {
        "profile.password_manager_enabled": False,  # Desativa o gerenciador de senhas
        "credentials_enable_service": False  # Desativa o serviço de credenciais
    })
    # Opções de rede e cache
    options.add_argument("--enable-async-dns")
    options.add_argument("--enable-quic")
    options.add_argument("--disk-cache-size=0")
    options.add_argument("--media-cache-size=0")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--max-connections-per-host=20")

    # Definindo o user-agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    # Modo headless
    options.add_argument("--headless")

    return options
