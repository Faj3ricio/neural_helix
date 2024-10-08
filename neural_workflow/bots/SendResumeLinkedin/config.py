import os
from dotenv import load_dotenv

env_path = os.path.abspath(os.path.join(os.getcwd(), '../../..', '.env'))
load_dotenv(dotenv_path=env_path)

#ex: ["Chrome"] or ["Firefox"]. WID A ideia e utilizar o chrome e firefox, certos sites bloqueam funcionalidades do chrome.
browser = ["Chrome"]
# Linkedin credentials
email = os.getenv('LINKEDIN_USER')
password = os.getenv('LINKEDIN_PASS')

headless = True
displayWarnings = False
firefoxProfileRootDir = r""

chromeProfilePath = r""

location = ["Belo Horizonte"]
# ex: ["Cargo 1","Cargo 2","Cargo 3", "Cargo 4"] #Isso aqui e ilimitado, pode utilizar quantos voce quiser
keywords = ["Analista de Dados","Engenheiro de Dados","Desenvolvedor Python", "Analista de BI","Cientista de Dados", "Desenvolvedor RPA"]

# ex:  ["Internship", "Entry level" , "Associate" , "Mid-Senior level" , "Director" , "Executive"] - OBRIGATORIO
experienceLevels = [ "Associate" ]

# ex: ["Any Time", "Past Month" , "Past Week" , "Past 24 hours"] - ATENÇÃO: SELECIONE SOMENTE 1
# Bug Report: Não consigo utilizar 24 hrs, tenho que modificar a logica. (Variavel "datePosted")
datePosted = ["Any Time"]

# ex:  ["Full-time", "Part-time" , "Contract" , "Temporary", "Volunteer", "Intership", "Other"]
jobType = ["Full-time", "Part-time" , "Contract"]

#ex: ["On-site" , "Remote" , "Hybrid"]
remote = ["On-site" , "Remote" , "Hybrid"]

#ex:["R$40,000+", "R$60,000+", "R$80,000+", "R$100,000+", "R$120,000+", "R$140,000+", "R$160,000+", "R$180,000+", "R$200,000+" ] - ATENÇÃO: SELECIONE SOMENTE 1
salary = [""]

# ex:["Recent"] or ["Relevent"] - ATENÇÃO: SELECIONE SOMENTE 1
sort = ["Relevent"]

#ex: ["Google"]
blacklistCompanies = []

# ex:["Assistente de TI", "JavaScript"]
blackListTitles = []

# Seguir companhia ?
followCompanies = False

# WIP - NÃO RELA A MÃO
preferredCv = 1
outputSkippedQuestions = True
useAiAutocomplete = False
onlyApplyCompanies = []
onlyApplyTitles = [] 
blockHiringMember = [] 
onlyApplyHiringMember = [] 
onlyApplyMaxApplications = []
onlyApplyMinApplications = []
onlyApplyJobDescription = []
blockJobDescription = []
onlyAppyMimEmployee = []
onlyApplyLinkedinRecommending = False
onlyApplySkilledBages = False
saveBeforeApply = False
messageToHiringManager = ""
listNonEasyApplyJobsUrl = False
defaultRadioOption = 1
answerAllCheckboxes = ""
outputFileType = [".txt"]