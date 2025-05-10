import datetime

def TimeKeeper() -> str:
    """ 
        Allows the AI agent to find the current time when the user requests it.
        Parameters: "None"
        Returns:    str: The current formatted time.
    """
    now = datetime.datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    day_of_week = now.strftime("%A")
    return f"Current time: {formatted_time} ({day_of_week})"
