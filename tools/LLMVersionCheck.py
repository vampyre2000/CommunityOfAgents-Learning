import requests
import datetime
from bs4 import BeautifulSoup

GLOBAL_DISRUPTION = datetime.date(2027,9,30)  #Date when we believe that the global disruption will happen.(Massive job loss due to automation)
AGI_DATE          = datetime.date(2029,10,30) #Date when we believe that AGI will happen. 
SINGULARITY_DATE  = datetime.date(2035,9,30)  #Date when we believe that the singularity will happen.

#Set the list of software versions that we are keeping tabs on
Software_versions={
                "LlamaCPP"     :"https://github.com/ggerganov/llama.cpp/releases/latest",
                "Koboldcpp"    :"https://github.com/LostRuins/koboldcpp/releases/latest",
                "KoboldcppROCM":"https://github.com/YellowRoseCx/koboldcpp-rocm/releases/latest",
                "Ollama"       :"https://github.com/ollama/ollama/releases/latest",
                "SillyTavern_M":"https://github.com/SillyTavern/SillyTavern/releases/latest",
                "GPT4All"      :"https://github.com/nomic-ai/gpt4all/releases/latest",
                "Fabric"       :"https://github.com/danielmiessler/fabric/releases/latest",
                "CrewAi"       :"https://github.com/crewAIInc/crewAI/releases/latest",
                "Autogen"      :"https://github.com/microsoft/autogen/releases/latest",
                "Agency Swarm" :"https://github.com/VRSEN/agency-swarm/releases/latest"
                }

# Get today's date and time using the datetime.date() function
today = datetime.date.today()
# Print the formatted date in "YYYY-MM-DD" format
# Send an HTTP GET request to retrieve the HTML content

def get_llm_versions() -> str:
    """
    Allows the AI agent to find the current versions of common LLM front/backends.
    Parameters: "None"
    Returns: str: A formatted string of the current versions of the software
    """
    results = []
    for program in Software_versions:
        URL = Software_versions[program] # Send an HTTP GET request to retrieve the HTML content
        response = requests.get(URL)
        if response.status_code == 200: # Check if the request was successful (status code 200)
            soup = BeautifulSoup(response.text, "html.parser") # Parse the HTML content using BeautifulSoup
            # Locate the element containing the version information (e.g., a <span> or <p> tag)
            version_element = soup.find("title")  # Adjust the selector based on the website's HTML structure
            date_element    = soup.find("relative-time")
            Version_f       = soup.find("relative-time")
            # Extract the version number from the element's text content
            version = version_element.text
            version_p = version.find("·")
            date = date_element.text.strip()
            results.append(f"Release Date {date}:{program}:{version[0:version_p]}")
        else:
            results.append(f"Failed to fetch the webpage for {program}")
    return "\n".join(results)

def get_disruption_dates() -> str:
    """
    Allows the AI agent to find the dates of the global disruption, AGI, and the singularity.
    Parameters: "None"
    Returns: str: String of the dates of the global disruption, AGI, and the singularity
    """
    disruption_days= (GLOBAL_DISRUPTION - today)
    AGI_days=        (AGI_DATE - today)
    singularity_days=(SINGULARITY_DATE - today)
    return (f"Today's date is the {today.strftime('%Y-%m-%d')}\n"
            f"Global disruption date: {GLOBAL_DISRUPTION} Days until global disruption: {disruption_days.days}\n"
            f"AGI date: {AGI_DATE} Days until AGI: {AGI_days.days}\n"
            f"Singularity date: {SINGULARITY_DATE} Days until the singularity: {singularity_days.days}")

