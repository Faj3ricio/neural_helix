"""
╔═════════════════╗
║Sieg module steps║
╚═════════════════╝
Carry out the entire procedure until extraction.
"""
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from webdriver_manager.chrome import ChromeDriverManager

from core.singleton.webdriver_singleton import WebDriverSingleton
from core.utils.utils import CrawlerManagements
from core.configs.config import load_dotenv


class StepsManipulationLinkedin:
    """
    Carry out the steps until you reach the jobs data
    """

    def __init__(self):
        self.driver = WebDriverSingleton.get_instance().get_driver()
        self.cm = CrawlerManagements()
        self.url_base_app_easy = None
        self.job_ids = None
        self.value_page = None

    def orchestrador(self):
        """
        Orchestrates the functions
        """
        self.linkedin_login()
        self.capture_apply_easily_data()

    def linkedin_login(self):
        """
        Perform the page login process
        """
        email_lin = os.getenv("EMAIL_LINKEDIN")
        pass_lin = os.getenv("PASSWORD_LINKEDIN")

        url_login = self.cm.validation_url('https://www.linkedin.com/uas/login',
                                           'Entrar')
        input_email = self.cm.validation_element('ID',
                                                 'username',
                                                 5).send_keys(email_lin)
        input_password = self.cm.validation_element('ID',
                                                    'password',
                                                    5).send_keys(pass_lin)
        submit_login = self.cm.validation_element('CLASS',
                                                  'btn__primary--large',
                                                  5).click()

    def capture_apply_easily_data(self):

        self.url_base_app_easy = 'https://www.linkedin.com/jobs/collections/recommended/?currentJobId='
        url_app_easy = self.cm.validation_url(self.url_base_app_easy,
                               'Vagas que mais combinam com seu perfil')

        self.driver.implicitly_wait(10)

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "job-card-job-posting-card-wrapper")))

        # Captura todos os blocos de vagas
        job_cards = self.driver.find_elements(By.CLASS_NAME, "job-card-job-posting-card-wrapper")

        self.job_ids = set()

        for job_card in job_cards:
            try:
                self.driver.execute_script("window.scrollTo(-20840404, document.body.scrollHeight);")
                time.sleep(3)
                # Verifica se há "Candidatura simplificada" dentro do card
                if "Candidatura simplificada" in job_card.text:
                    job_id = job_card.get_attribute("data-job-id")
                    print(job_id)
                    if job_id:
                        self.job_ids.add(job_id)  # Adiciona ao set (evita duplicatas)

                    self.value_page += 24
                    next_url = f"{self.url_base_app_easy}&start={self.value_page}"
                    self.cm.validation_url(next_url,
                                           'Vagas que mais combinam com seu perfil')
                    time.sleep(3)
                    if self.value_page > 240:
                        print(f'Numero de Jobs: {len(self.job_ids)}')
                        break

            except Exception as e:
                print(e)
                continue


spider_linkedin = StepsManipulationLinkedin()
spider_linkedin.orchestrador()
