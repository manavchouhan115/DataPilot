import os
import uuid
import httpx
from typing import TypedDict, Annotated, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# State
class GraphState(TypedDict):
    nl_description: str
    pipeline_id: str
    config: Dict[str, Any]
    current_data: list
    status: str
    error: str

# Schema for LLM extraction
class PipelineConfig(BaseModel):
    source_path: str
    transformations: Dict[str, str]
    destination_path: str
    table_name: str

# LLM Node: Planner
def plan_pipeline(state: GraphState):
    llm = ChatGroq(model_name="llama-3.3-70b-versatile") # using Groq
    
    # We use LLM with structured output to parse the NL into a config
    structured_llm = llm.with_structured_output(PipelineConfig)
    
    prompt = f"""You are a planner agent for an ETL pipeline.
Convert the user request into a pipeline configuration.
User Request: {state['nl_description']}

Assume source is "data/input.csv" and destination is "data/destination.db" with table name "users" unless specified otherwise.
Return transformations as a dictionary, where key is column name and value is the operation (e.g. "uppercase").
"""
    try:
        config = structured_llm.invoke(prompt)
        # Handle case where LLM returns object or dict
        if hasattr(config, "model_dump"):
            config_dict = config.model_dump()
        else:
            config_dict = dict(config)
            
        return {"config": config_dict, "status": "planning_complete"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

# Executor Nodes
def execute_extract(state: GraphState):
    if state.get("error"):
        return state
    
    config = state["config"]
    url = "http://localhost:8001/extract"
    try:
        response = httpx.post(url, json={"source_path": config["source_path"]}, timeout=30.0)
        response.raise_for_status()
        data = response.json()["data"]
        return {"current_data": data, "status": "extracted"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def execute_transform(state: GraphState):
    if state.get("error"):
        return state
        
    config = state["config"]
    url = "http://localhost:8002/transform"
    try:
        response = httpx.post(url, json={
            "data": state["current_data"],
            "transformations": config["transformations"]
        }, timeout=30.0)
        response.raise_for_status()
        data = response.json()["data"]
        return {"current_data": data, "status": "transformed"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def execute_load(state: GraphState):
    if state.get("error"):
        return state
        
    config = state["config"]
    url = "http://localhost:8003/load"
    try:
        response = httpx.post(url, json={
            "data": state["current_data"],
            "destination": config["destination_path"],
            "table_name": config["table_name"]
        }, timeout=30.0)
        response.raise_for_status()
        return {"status": "completed", "current_data": []}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

# Graph Definition
builder = StateGraph(GraphState)

builder.add_node("planner", plan_pipeline)
builder.add_node("extractor", execute_extract)
builder.add_node("transformer", execute_transform)
builder.add_node("loader", execute_load)

builder.add_edge(START, "planner")

# Route logic
def router(state: GraphState):
    if state.get("error"):
        return END
    return "extractor"

builder.add_conditional_edges("planner", router)

def router_extract(state: GraphState):
    if state.get("error"):
        return END
    return "transformer"
    
builder.add_conditional_edges("extractor", router_extract)

def router_transform(state: GraphState):
    if state.get("error"):
        return END
    return "loader"

builder.add_conditional_edges("transformer", router_transform)
builder.add_edge("loader", END)
