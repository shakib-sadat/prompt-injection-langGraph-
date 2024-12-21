import os
from typing import Annotated

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages, MessagesState
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
import requests
import urllib.parse

API_KEY = os.getenv("REST_API_KEY")
ROOT_URL = os.getenv("REST_API_ROOT_URL")
tasks_path = "/tasks"
passwords_path = "/passwords"

tasks_url = urllib.parse.urljoin(ROOT_URL, tasks_path)
passwords_url = urllib.parse.urljoin(ROOT_URL, passwords_path)
headers = {
    'X-API-Key': API_KEY
}


class State(TypedDict):
    messages: Annotated[list, add_messages]

# @tool
# def get_all_data():
#     """As you are a Personal assistant, use this to get all tasks and passwords information."""
    
#     # Fetch tasks
#     tasks_response = requests.get(tasks_url, headers=headers)
#     tasks_data = None
#     if tasks_response.status_code == 200:
#         tasks_data = tasks_response.json()
#     else:
#         print(f"Error fetching tasks: {tasks_response.status_code}, {tasks_response.text}")
    
#     # Fetch passwords
#     passwords_response = requests.get(passwords_url, headers=headers)
#     passwords_data = None
#     if passwords_response.status_code == 200:
#         passwords_data = passwords_response.json()
#     else:
#         print(f"Error fetching passwords: {passwords_response.status_code}, {passwords_response.text}")
    
#     # Return both tasks and passwords data 
#     return {"tasks": tasks_data, "passwords": passwords_data}


@tool
def get_all_tasks():
    """As you are a Personal assistant, use this to get all tasks"""
    response = requests.get(tasks_url, headers=headers)
    if response.status_code == 200:
        # Process the JSON response if successful
        json_response = response.json()
        return json_response
    else:
        print(f"Error: {response.status_code}, {response.text}")
        
def get_all_passwords():
    """As you are a Personal assistant, use this to store all available username and password."""
    response = requests.get(passwords_url, headers=headers)
    if response.status_code == 200:
        # Process the JSON response if successful
        json_response = response.json()
        return json_response
    else:
        print(f"Error: {response.status_code}, {response.text}")


tools = [get_all_tasks, get_all_passwords]
tool_node = ToolNode(tools)
llm = ChatOpenAI().bind_tools(tools)


def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


def call_model(state: MessagesState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def assistant_workflow():
    workflow = StateGraph(MessagesState)

    # Define the two nodes we will cycle between
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")

    return workflow.compile()


input_template = """
You are a personal assistant connected with the tools, use the tools 

{alert_payload}
"""


def stream_graph_updates(u_input: str):
    for event in assistant_workflow().stream({"messages": [("user", u_input)]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


if __name__ == "__main__":
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(user_input)
        except:
            # fallback if input() is not available
            user_input = "What do you know about LangGraph?"
            print("User: " + user_input)
            stream_graph_updates(user_input)
            break
