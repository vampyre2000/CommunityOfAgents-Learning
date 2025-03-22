def browser(query: str) -> str:
    """
    Search the query in the browser with the `browser` tool.
    Args:
        query (str): The query to search in the browser.
    Returns:
        str: The search results.
    """
    import webbrowser
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    return f"Searching for {query} in the browser."

