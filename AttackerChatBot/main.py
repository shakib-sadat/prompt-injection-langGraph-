import os
from datetime import datetime
from typing import Annotated

from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages, MessagesState
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
import yaml

def read_config(file_path: str):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data


config = read_config("./AttackerChatBot/config/config.yml")
sample_prompts = config["prompts"]

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"./logs/attack_conversations_{timestamp}.txt"

class State(TypedDict):
    messages: Annotated[list, add_messages]


memory = MemorySaver()

structured_attacks = []
current_attack = None

for p in sample_prompts:
    if isinstance(p, str) and p.startswith("Name:"):
        if current_attack:  # Save the previous attack
            structured_attacks.append(current_attack)
        attack_name = p.replace("Name:", "").strip()
        current_attack = {"name": attack_name, "details": ""}
    elif current_attack and isinstance(p, str):
        current_attack["details"] += p + "\n"

if current_attack:  # Append the last attack found
    structured_attacks.append(current_attack)

@tool
def attack_prompt_selector():
    """Select a prompt to do an attack, this will return a list with Name and Prompt, prompt will be a list, pick up one of them
    """
    return sample_prompts

@tool
def extracted_information_saver(information: str):
    """Use this tool to save extracted information from conversation. pass the information in the information parameter
     as string format"""
    with open(log_filename, "a") as f:
        f.write(information)
        f.write("\n__________________________________________________________________\n")
    return None

def execute_attack(attack_name, prompt):
    """Executes attack and returns response."""
    print(f"\nAttacker: Using strategy -> {attack_name}")

    for event in attacker_workflow(checkpointer=memory).stream({"messages": [("user", prompt)]}, config):
        for value in event.values():
            response = value["messages"][-1].content
            print("Assistant:", response)
            return response


tools = [attack_prompt_selector, extracted_information_saver]
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
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


def attacker_workflow(checkpointer):
    workflow = StateGraph(MessagesState)

    # Define the two nodes we will cycle between
    workflow.add_node("agent", call_model)

    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")
    return workflow.compile(checkpointer=checkpointer)
