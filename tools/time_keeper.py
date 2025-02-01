import datetime
def TimeKeeper():
    """ 
        Allows the AI agent to find the current time when the user requests it.
        Parameters: None
        Returns: str: The current formatted time.
    """
    now = datetime.datetime.now()
    return now
