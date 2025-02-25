"""
╔═════════════════╗
║Sieg module steps║
╚═════════════════╝
Carry out the entire procedure until extraction.
"""
from facss_datastream.core.webdriver_singleton import WebDriverSingleton

class StepsManipulationLinkedin:
    """
    Carry out the steps until you reach the jobs data
    """

    def __init__(self):
        self.driver = WebDriverSingleton.get_instance().get_driver()

    def orchestrador(self):
        """
        Orchestrates the functions
        """
        self.linkedin_login()

    def linkedin_login(self):
        """
        WIP
        """
        pass