"""
╔══════════════════════╗
║Singleton do Webdriver║
╚══════════════════════╝
Centralization of the webdriver used in several projects
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
import os
import sys

class WebDriverSingleton:
    """
    Main class to be imported into other modules
    """
    _instance = None

    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Detects the operating system and sets the appropriate driver path
        if os.name == "nt":  # Windows
            chrome_driver_path = os.path.join(current_dir, 'chromedriver.exe')
        elif os.name == "posix" and "linux" in sys.platform:  # Linux
            chrome_driver_path = os.path.join(current_dir, 'chromedriver_linux')
            os.chmod(chrome_driver_path, 0o755)
        else:
            raise Exception("Sistema operacional não suportado!")

        # Configures the Chrome service with the appropriate driver
        service = ChromeService(executable_path=chrome_driver_path, log_output=os.devnull)

        # Initialize the singleton driver
        self.driver = webdriver.Chrome(service=service)

    @classmethod
    def get_instance(cls):
        """
        Returns the single instance of WebDriverSingleton.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_driver(self):
        """
        Returns the singleton driver.
        """
        return self.driver
