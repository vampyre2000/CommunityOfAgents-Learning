import datetime
def TimeKeeper() -> str:
    """ 
        Allows the AI agent to find the current time when the user requests it.
        Parameters: "None"
        Returns:    str: The current formatted time.
    """
    return datetime.datetime.now()
