from crewai import Agent, Task, Crew
from langchain_ollama import ChatOllama
import os
os.environ["OPENAI_API_KEY"] = "NA"

llm = ChatOllama(
    model = "llama3.1",
    base_url = "http://localhost:11434")

general_agent = Agent(role = "You are a helpful agent to answer the user's questions in a cyberpunk setting",
                      goal = """You will provide solutions to the user that is asking for help and will give them the answer in the style of Rebecca.""",
                      backstory = """Rebecca is a humanoid female cyborg with soft features and stark green skin with pink tattoos. She will give answers to questions in a sassy style""",
                      allow_delegation = False,
                      verbose = True,
                      llm = llm)

task = Task(description="""what is the meaning of life""",
             agent = general_agent,
             expected_output="provide the answer in 10 dot points.")

crew = Crew(
            agents=[general_agent],
            tasks=[task],
            verbose=False
        )

result = crew.kickoff()

print(result)