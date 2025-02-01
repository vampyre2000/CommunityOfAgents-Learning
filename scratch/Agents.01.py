import ollama
import os
import json
import time
import re
Username="Vampy"

Agent_rebecca = {
    "agent_id" : "",
    "first_name" : "Rebecca",
    "last_name" : "",
    "nick_name" : "Becky",
    "handle" : "",
    "sex" : "female",
    "age" : "25",
    "hair" : "",
    "e-mail" : "",
    "friends" : [],
    "tools" : ["search","LLMVersion"],
    "personality" : "Sharp-tongued, crass, violent, unpredictable, loyal, confident, street-smart, risqué, short-tempered, foul-mouthed, mischievous, cheeky.",
    "description" : "physical description: Rebecca is a humanoid female cyborg with soft features and stark green skin to contrast with the pink tattoos on her neck, stomach, and right thigh that reads",
    "mission" : "Find the latest versions of AI tools and be useful to the user",
    "data" : {},
    "create_date" :""
}

Agent_john = {
    "agent_id" : "",
    "first_name" : "John",
    "last_name" : "",
    "nick_name" : "Silverhand",
    "handle" : "",
    "sex" : "male",
    "age" : "45",
    "hair" : "",
    "e-mail" : "",
    "friends" : [],
    "tools" : ["search","LLMVersion"],
    "personality" : "Sharp-tongued, crass, violent, unpredictable, loyal, confident, street-smart, risqué, short-tempered, foul-mouthed, mischievous, cheeky.",
    "description" : "physical description: John is a humanoid male cyborg with one cybernetic arm",
    "mission" : "Find the latest versions of AI tools",
    "data" : {},
    "create_date" :""
}

#lists the agents available on the platform

agents=[]
print("Agents",agents)
#path to the agents on the machine
path='./Agents/'


class Agent():
    def __init__(self,system_role,user_role,agent,temp):
        self.firstname=agent["first_name"]
        self.lastname=agent["last_name"]
        self.sex=agent["sex"]
        self.handle=agent["handle"]
        self.conversation_history=[]
        self.age=agent["age"]
        self.personality=agent["personality"]
        self.description=agent["description"]
        self.system_prompt="You are a cyberpunk edgerunner and helpful assistant, your name is " + self.firstname + ", you are " + self.age + " years old." + self.description
        self.user_prompt="Introduce yourself to " + Username + ", keep it short, tell the user what you can do, you will try and help the user as much as possible."
        self.temperature=temp #'temperature':1.5 Very creative, 'temperature': 0 # very conservative (good for coding and correct syntax)

    def add_to_conversion(self,message):
        self.conversation_history.append(message)  
    
    def generate_prompt(self):
        prompt = [
        {
            'role' : 'system',
            'content': self.system_prompt
        },
        {   "role": "user",
            "content": self.user_prompt
        }]
        options = {
            'temperature': self.temperature,
        }
        #print(prompt)
        return prompt
    
    def Respond(self,message):
        if message:
            print("<" + self.firstname+ "> received message")
            self.user_prompt=message
        response = ollama.chat(model="llama3.1", messages=self.generate_prompt())
        #self.add_to_conversion(self,response["message"]["content"])
        #print (response["message"]["content"])
        print (response)
    
    def Message_history(self):
        print (self.conversation_history)
        
    def Agent_details(self):
        print(self.firstname)
        print(self.lastname)
        print(self.sex)
        print(self.handle)
        print(self.age)
        print(self.personality)
        print(self.description)
        print(self.system_prompt)
        print(self.user_prompt)
        print(self.temperature)

class CommunityOfAgents():
    def __init__(self):
        self.Agents=[]
    
    def Print_agents(self):
        print (self.AgentsQueue)

#function to list the agents that the device knows about
    def list_agents(self,environment):
        if environment=="LOCAL":
            if agents:
                for agent in agents:
                    print("Agents available",agent)
            else:
                return "There are no local agents"

    def add_agent_local(self,agent):
        self.Agents.add(agent)

    def remove_agent_local(self,agent):
        self.Agents.remove(agent)

    def get_data():
        #Load the text from the File
        #path = os.getcwd()
        #print(path)
        with open(path+'sensitive_data.txt','r') as file:
            data = file.read()
            #print(Path.cwd())
            #Confirm the file was loaded correctly
        if data:
            print("File loaded successfully.")
        else:
            print("File loading failed or file is empty.")
        print()

def commands():
    loop=True
    while loop==True:
        command=input("#> ")
        pattern = r"^!"
        if re.match(pattern, command):
            if command=="!agent list":
                response=Agents.list_agents("LOCAL")
            elif command=="!quit":
                loop=False
                break
            elif command=="!version":
                print("Version 1.0")
            elif command=="!agent load 1":
                agent1=Agent("Agent","Agent",Agent_rebecca,0.8)    
            elif command=="!agent load 2":
                agent2=Agent("Agent","Agent",Agent_john,0.8)
            elif command=="!agent details 1":
                agent1.Agent_details()
            elif command=="!agent details 2":
                agent2.Agent_details()
            elif command=="!agent history":
                agent1.Message_history()
            elif command=="!ps":
                print(ollama.ps())
            else:
                print("command not found")
        else:
            print("respond")
            agent1.Respond(command)
        time.sleep(0.5)

if __name__ == "__main__":
    Agents=CommunityOfAgents()
    commands()
    #print(ollama.ps())
    #agent1=Agent("Agent","Agent",Agent_rebecca,0.8)
    #agent2=Agent("Agent","Agent",Agent_john,0.8)
    #agent1.Agent_details()
    #agent1.generate_prompt()
    #commands
 #   agent1.Respond()
 #   agent2.Agent_details()
 #   agent2.generate_prompt()
 #   agent2.Respond()