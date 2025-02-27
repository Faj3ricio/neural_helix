"""
╔═════════════════╗
║Sieg module steps║
╚═════════════════╝
Carry out the entire procedure until extraction.
"""
import time

from core.singleton.webdriver_singleton import WebDriverSingleton
from core.utils.utils import CrawlerManagements


class StepsManipulationLinkedin:
    """
    Carry out the steps until you reach the jobs data
    """

    def __init__(self):
        self.driver = WebDriverSingleton.get_instance().get_driver()
        self.cm = CrawlerManagements()

    def orchestrador(self):
        """
        Orchestrates the functions
        """
        self.linkedin_login()

    def linkedin_login(self):
        """
        Perform the page login process
        """
        self.cm.validation_url('https://www.linkedin.com/uas/login',
                               'Entrar')
        self.cm.validation_element('ID',
                                   'username',
                                   5).click()
        time.sleep(5)

        pass


spider_linkedin = StepsManipulationLinkedin()
spider_linkedin.orchestrador()
