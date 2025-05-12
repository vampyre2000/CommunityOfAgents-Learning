import webbrowser

def browser(query: str) -> str:
    """
    Search the query in the browser with the `browser` tool.
    Args:     query (str): The query to search in the browser.
    Returns:  str: The search results.
    """
    
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    return f"Searching for {query} in the browser."

def Openwebsite(site: str) -> str:
    """
    Opens up the browser to the website that the user wants to see.
    Args:     query (str): The query to search in the browser.
    Returns:  str: The search results.
    """

    url = {site}
    webbrowser.open(site, new=2)
    return f"Opening {site} in the browser."

def test():
    anime=f"https://hianimez.to/home"
    youtube=f"https://www.youtube.com/"
    github=f"https://github.com/vampyre2000/CommunityOfAgents-Learning"
    discord=f"https://discord.com"
    Openwebsite(anime)