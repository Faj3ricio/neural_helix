import time, math, random, os
import utils, constants, config
import pickle, hashlib

from selenium import webdriver
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

from loguru import logger as log

# Logs
log.add(
    'logs.txt',
    format='<g>{time}</g> | <r>{level}</r> | <c>{thread}</c>  <m>{function}</m>:<m>{line}</m> - <y>{message}</y>',
    level="DEBUG"
    # Implementar o envio de email caso CRITICAL v3.1
)


class Linkedin:
    def __init__(self):
        utils.prYellow("🤖 Obrigado por usar o meu bot. Use com moderação !!!")
        utils.prYellow("🌐 O bot será executado no navegador Chrome e fará login no Linkedin para você.")
        self.driver = webdriver.Chrome(options=utils.chromeBrowserOptions())
        cookies_directory = os.path.join(os.getcwd(),
                                         'cookies')  # Cria um diretório para armazenar os cookies. Para consumir mais tarde ...
        log.debug(f'Diretorio de cokkies criado com sucesso !!!\n{cookies_directory}')
        if not os.path.exists(cookies_directory):
            os.makedirs(cookies_directory)
        self.cookies_path = f"{cookies_directory}/{self.getHash(config.email)}.pkl"
        log.debug(f'Pasta de cokkies criado com sucesso !!!\n{self.cookies_path}')
        self.driver.get('https://www.linkedin.com')
        self.loadCookies()

        if not self.isLoggedIn():  # Etapa de login, caso de um erro volta a mensagem
            self.driver.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
            utils.prYellow("🔄 Tentando entrar no Linkedin...")
            try:
                self.driver.find_element("id", "username").send_keys(config.email)
                time.sleep(2)
                self.driver.find_element("id", "password").send_keys(config.password)
                time.sleep(2)
                self.driver.find_element("xpath", '//button[@type="submit"]').click()
                time.sleep(30)
            except:
                utils.prRed(
                    "❌ Não foi possível fazer login no Linkedin usando o Chrome. Verifique suas credenciais do Linkedin nas linhas 7 e 8 dos arquivos de configuração do arquivo 'config.py'")

            self.saveCookies()
        # Startar Aplicação
        self.linkJobApply()

    def getHash(self,
                string):  # Criar um identificador único para o cookies, garantindo que cada usuário tenha seu próprio arquivo de cookies. USEI COMO PARAMETRO O EMAIL
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    def loadCookies(self):  # Carrega os cookies salvos, se existirem ...
        if os.path.exists(self.cookies_path):
            cookies = pickle.load(open(self.cookies_path, "rb"))
            self.driver.delete_all_cookies()
            for cookie in cookies:
                self.driver.add_cookie(cookie)

    def saveCookies(self):  # Responsável por salvar os cookies após o login.
        pickle.dump(self.driver.get_cookies(), open(self.cookies_path, "wb"))

    def isLoggedIn(self):  # Verifica se o usuário está logado.
        self.driver.get('https://www.linkedin.com/feed')
        try:
            self.driver.find_element(By.XPATH, '//*[@id="ember14"]')
            return True
        except:
            pass
        return False

    def generateUrls(self):  # Gera URLs de emprego no LinkedIn, e cria diretorio 'data' de existir
        if not os.path.exists('data'):
            os.makedirs('data')
        try:
            with open('data/urlData.txt', 'w', encoding="utf-8") as file:
                linkedinJobLinks = utils.LinkedinUrlGenerate().generateUrlLinks()
                for url in linkedinJobLinks:
                    file.write(url + "\n")
            utils.prGreen("✅ As URLs de aplicação foram criados com sucesso, agora o bot visitará esses URLs.")
        except:
            utils.prRed(
                "❌ Não foi possível gerar URLs, certifique-se de ter editado a linha 25-39 do arquivo 'config.py'")

    def linkJobApply(
            self):  # Byg Report: Ao acabar de enviar, ele fecha, entao por exemplo se tiver uma vaga ele fecha assim quando envia para ela, preciso entender o que esta acontecendo
        self.generateUrls()  # Gera as URLs de emprego
        countApplied = 0  # Contador
        countJobs = 0

        urlData = utils.getUrlDataFile()  # Obtém os dados das URLs de emprego do arquivo

        # Loop sobre cada URL de emprego
        for url in urlData:
            # Navegando até a URL de emprego
            self.driver.get(url)
            time.sleep(random.uniform(1, constants.botSpeed))

            totalJobs = self.driver.find_element(By.XPATH, '//small').text  # Obtem numero total de empregos da pagina
            totalPages = utils.jobsToPages(totalJobs)

            urlWords = utils.urlToKeywords(
                url)  # Converte URL em palavras-chave para exibir e intera sobre as pginas de resultados dos trabalhos disponiveis.
            lineToWrite = "- Categoria: " + urlWords[0] + " - Localizacao: " + urlWords[
                1] + " - Foram aplicados " + str(totalJobs) + " de cargos."  # Insere as informaçoes no 'data'.
            self.displayWriteResults(lineToWrite)

            # Iterando sobre as páginas de resultados dos trabalhos disponíveis
            for page in range(totalPages):
                # Calcula o índice de início para cada página de resultados, com base no número de empregos por página. Isso é usado para navegar para a próxima página de resultados.
                currentPageJobs = constants.jobsPerPage * page
                url = url + "&start=" + str(currentPageJobs)
                # Navega para a próxima página
                self.driver.get(url)
                time.sleep(random.uniform(1, constants.botSpeed))
                # Obtem os IDs dos trabalhos disponíveis na página atual ESSA AQUI E A NATA DO BOLO EM
                offersPerPage = self.driver.find_elements(By.XPATH, '//li[@data-occludable-job-id]')
                offerIds = [(offer.get_attribute(
                    "data-occludable-job-id").split(":")[-1]) for offer in offersPerPage]
                time.sleep(random.uniform(1, constants.botSpeed))

                # Verifica se os trabalhos já foram aplicados anteriormente. Se não, adiciona seus IDs à lista
                for offer in offersPerPage:
                    if not self.element_exists(offer, By.XPATH, ".//*[contains(text(), 'Applied')]"):
                        offerId = offer.get_attribute("data-occludable-job-id")
                        offerIds.append(int(offerId.split(":")[-1]))
                # Itera sobre os IDs dos trabalhos disponíveis na página atual e constrói a URL da página de detalhes do trabalho.
                for jobID in offerIds:
                    offerPage = 'https://www.linkedin.com/jobs/view/' + str(jobID)
                    self.driver.get(offerPage)
                    time.sleep(random.uniform(1, constants.botSpeed))

                    countJobs += 1
                    # Obtem as propriedades do trabalho atual, E VERIFICA SE ELE ESTA NA BLACKLIST SE ELE TIVER NA BLACKLIST retorna mensagem
                    jobProperties = self.getJobProperties(countJobs)
                    if "blacklisted" in jobProperties:
                        lineToWrite = jobProperties + " | " + "* 🤬 Trabalho na lista negra, ignorado!: " + str(
                            offerPage)
                        self.displayWriteResults(lineToWrite)

                    else:
                        easyApplybutton = self.easyApplyButton()  # Verifica se o botão está disponível na página do trabalho

                        if easyApplybutton is not False:
                            easyApplybutton.click()
                            time.sleep(random.uniform(1, constants.botSpeed))

                            try:
                                self.chooseResume()  # Tenta escolher o currículo e clicar no botão
                                self.driver.find_element(By.CSS_SELECTOR,
                                                         "button[aria-label='Enviar candidatura']").click()
                                time.sleep(random.uniform(1, constants.botSpeed))
                                # Registro do resultado da aplicação bem-sucedida !!!
                                lineToWrite = jobProperties + " | " + "* 🥳 Acabei de me candidatar a esta vaga: " + str(
                                    offerPage)
                                self.displayWriteResults(lineToWrite)
                                countApplied += 1

                            except:
                                try:
                                    self.driver.find_element(By.CSS_SELECTOR,
                                                             "button[aria-label='Avançar para próxima etapa']").click()
                                    time.sleep(random.uniform(1, constants.botSpeed))
                                    self.driver.find_element(By.CSS_SELECTOR,
                                                             "button[aria-label='Revise sua candidatura']").click()
                                    time.sleep(random.uniform(1, constants.botSpeed))
                                    self.driver.find_element(By.CSS_SELECTOR,
                                                             "button[aria-label='Enviar candidatura']").click()
                                    time.sleep(random.uniform(1, constants.botSpeed))
                                    self.chooseResume()
                                    # comPercentage = self.driver.find_element(By.XPATH,
                                    #                                          'html/body/div[3]/div/div/div[2]/div/div/span').text
                                    # percenNumber = int(comPercentage[0:comPercentage.index("%")])
                                    # result = self.applyProcess(percenNumber, offerPage)
                                    lineToWrite = jobProperties + " | " + "* 🥳 Acabei de me candidatar a esta vaga: " + str(offerPage)
                                    self.displayWriteResults(lineToWrite)

                                except Exception:
                                    self.chooseResume()
                                    lineToWrite = jobProperties + " | " + "* 🥵 Não é possível se candidatar a esta vaga! " + str(
                                        offerPage)
                                    self.displayWriteResults(lineToWrite)
                        else:
                            lineToWrite = jobProperties + " | " + "* 🤷‍♂️ Já aplicado! Vaga: " + str(offerPage)
                            self.displayWriteResults(lineToWrite)

            # Exibindo um resumo dos empregos aplicados e totais
            utils.prYellow("Categoria: " + urlWords[0] + "," + urlWords[1] + " aplicado: " + str(
                countApplied) + " empregos: " + str(countJobs) + ".")

        # Chamando a função para finalizar o processo, que pode incluir a oportunidade de fazer uma doação
        utils.finish(self)

    def chooseResume(self):  # Seleciona CUrriculo
        try:
            self.driver.find_element(
                By.CLASS_NAME, "jobs-document-upload__title--is-required")
            resumes = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'ui-attachment--pdf')]")
            if (len(resumes) == 1 and resumes[0].get_attribute("aria-label") == "Selecione"):
                resumes[0].click()
            elif (len(resumes) > 1 and resumes[config.preferredCv - 1].get_attribute("aria-label") == "Selecione"):
                resumes[config.preferredCv - 1].click()
            elif (type(len(resumes)) != int):
                utils.prRed(
                    "❌ Nenhum currículo foi selecionado. Adicione pelo menos um currículo à sua conta do Linkedin.")
        except:
            pass

    def getJobProperties(self, count):  # Etapa da BlackList
        textToWrite = ""
        jobTitle = ""
        jobLocation = ""

        try:
            jobTitle = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'job-title')]").get_attribute(
                "innerHTML").strip()
            res = [blItem for blItem in config.blackListTitles if (blItem.lower() in jobTitle.lower())]
            if (len(res) > 0):
                jobTitle += "(Titulo BlackList: " + ' '.join(res) + ")"
        except Exception as e:
            if (config.displayWarnings):
                utils.prYellow("⚠️ Aviso ao obter jobTitle: " + str(e)[0:50])
            jobTitle = ""

        try:
            time.sleep(5)
            jobDetail = self.driver.find_element(By.XPATH,
                                                 "//div[contains(@class, 'job-details-jobs')]//div").text.replace("·",
                                                                                                                  "|")
            res = [blItem for blItem in config.blacklistCompanies if (blItem.lower() in jobTitle.lower())]
            if (len(res) > 0):
                jobDetail += "(empresa na lista negra: " + ' '.join(res) + ")"
        except Exception as e:
            if (config.displayWarnings):
                print(e)
                utils.prYellow("⚠️ Aviso ao obter jobDetail: " + str(e)[0:100])
            jobDetail = ""

        try:
            jobWorkStatusSpans = self.driver.find_elements(By.XPATH,
                                                           "//span[contains(@class,'ui-label ui-label--accent-3 text-body-small')]//span[contains(@aria-hidden,'true')]")
            for span in jobWorkStatusSpans:
                jobLocation = jobLocation + " | " + span.text

        except Exception as e
            if (config.displayWarnings):
                print(e)
                utils.prYellow("⚠️ Aviso ao obter jobLocation: " + str(e)[0:100])
            jobLocation = ""
        textToWrite = str(count) + " | " + jobTitle + " | " + jobDetail + jobLocation
        return textToWrite

    def easyApplyButton(self):  # Botao de candidatura simplificada
        try:
            time.sleep(random.uniform(1, constants.botSpeed))
            button = self.driver.find_element(By.XPATH,
                                              "//div[contains(@class,'jobs-apply-button--top-card')]//button[contains(@class, 'jobs-apply-button')]")
            EasyApplyButton = button
        except:
            EasyApplyButton = False

        return EasyApplyButton

    def applyProcess(self, percentage,
                     offerPage):  # Realiza toda a manipulação da aplicação do processo. WIP - Já consigo realizar a candidatura das vagas que não tem perguntas, preciso mapear as perguntas mais recentes e criar uma forma de enviar.
        applyPages = math.floor(100 / percentage) - 2
        result = ""
        for pages in range(applyPages):
            self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Avançar para próxima etapa']").click()


        self.driver.find_element(By.XPATH, "button[aria-label='Revise sua candidatura']").click()
        time.sleep(random.uniform(1, constants.botSpeed))

        if config.followCompanies is False:
            try:
                self.driver.find_element(By.CSS_SELECTOR, "label[for='follow-company-checkbox']").click()
            except:
                pass

        self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Enviar candidatura']").click()
        time.sleep(random.uniform(1, constants.botSpeed))

        result = "* 🥳 Acabei de me candidatar a esta vaga: " + str(offerPage)

        return result

    def displayWriteResults(self, lineToWrite: str):
        try:
            print(lineToWrite)
            utils.writeResults(lineToWrite)
        except Exception as e:
            utils.prRed("❌ Erro no DisplayWriteResult: " + str(e))

    def element_exists(self, parent, by, selector):
        return len(parent.find_elements(by, selector)) > 0


start = time.time()
Linkedin().linkJobApply()
end = time.time()
utils.prYellow("---Pegou: " + str(round((time.time() - start) / 60)) + " minute(s).")
