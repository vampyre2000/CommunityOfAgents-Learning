from bs4 import BeautifulSoup
import requests
import datetime

# Function to safely get text from a soup object, returning an empty string if None or no result
def safe_get_text(soup_object, selector):
    try:
        return str(next(soup_object.select(selector)))
    except Exception:
        return ""

# Function to check software version details
def check_version(program_name, url):
    """
    Retrieves the latest version and release date from a given URL.

    Args:
        program_name (str): Name of the software being checked.
        url (str): The base URL for the software's page.

    Returns:
        str: Formatted string with version info or an empty string if no data found.
    """
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch {url}")

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for elements that contain version information
        # These selectors may need adjustment based on the actual HTML structure of each site
        version_selector = 'div.version-info'  # Adjust as needed
        release_date_selector = 'meta[content*="Release Date"]'

        if not hasattr(soup, version_selector):
            raise Exception(f"Version selector '{version_selector}' does not exist.")
        if not hasattr(soup, release_date_selector):
            raise Exception(f"Release date selector '{release_date_selector}' does not exist.")

        version_info = safe_get_text(soup, version_selector)
        release_date = safe_get_text(soup, release_date_selector)

        if version_info and release_date:
            return f"{release_date} - {program_name}: {version_info}"
        else:
            return f"No version information available for: {program_name}"
    except Exception as e:
            print(f"Error checking {program}: {str(e)}")

# Main execution flow
def main():
    today = datetime.date.today()
    print(f"Current date: {today}")
    
    # List of software versions as before (unchanged)
    Software_versions = {
        "LlamaCPP": "https://github.com/ggerganov/llama.cpp/releases/latest",
        "Koboldcpp": "https://github.com/LostRuins/koboldcpp/releases/latest",
        "KoboldcppROCM": "https://github.com/YellowRoseCx/koboldcpp-rocm/releases/latest",
        "Ollama": "https://github.com/ollama/ollama/releases/latest",
        "SillyTavern_M": "https://github.com/SillyTavern/SillyTavern/releases/latest",
        "GPT4All": "https://github.com/nomic-ai/gpt4all/releases/latest",
        "Fabric": "https://github.com/danielmiessler/fabric/releases/latest",
        "CrewAi": "https://github.com/crewAIInc/crewAI/releases/latest",
        "Autogen": "https://github.com/microsoft/autogen/releases/latest",
        "Agency Swarm": "https://github.com/VRSEN/agency-swarm/releases/latest"
    }

    # Days until disruption
    global_disruption = datetime.date(2027, 9, 30)
    agi_date = datetime.date(2029, 10, 30)
    singularity_date = datetime.date(2030, 9, 30)

    print("Global Disruption Date:", global_disruption)
    print(f"Days until Global Disruption: {global_disruption - today}")
    
    print("AGI Date:", agi_date)
    print(f"Days until AGI: {agi_date - today}")

    print("Singularity Date:", singularity_date)
    print(f"Days until Singularity: {singularity_date - today}")

    # Check each software version
    for program in Software_versions:
        try:
            version_info = check_version(program, Software_versions[program])
            if version_info:
                print(f"\n{version_info}")
        except Exception as e:
            print(f"Error checking {program}: {str(e)}")

if __name__ == "__main__":
    main()

