import os
import uuid
import httpx
import logging
from typing import TypedDict, Annotated, Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# State
class PipelineState(TypedDict):
    nl_description: str
    pipeline_id: str
    config: Dict[str, Any]
    current_data: list
    status: str
    errors: List[str]
    logs: List[str]
    retry_count: int

# Schema for LLM extraction
class PipelineConfig(BaseModel):
    source_path: str
    transformations: Dict[str, str]
    destination_path: str
    table_name: str

# 1. Planner Agent
def planner_agent(state: PipelineState):
    logs = state.get("logs", []) or []
    errors = state.get("errors", []) or []
    logs.append("Planner: Starting mapping from NL to configuration.")
    
    llm = ChatGroq(model_name="llama-3.3-70b-versatile")
    structured_llm = llm.with_structured_output(PipelineConfig)
    
    prompt = f"""You are a planner agent for an ETL pipeline.
Convert the user request into a pipeline configuration.
User Request: {state['nl_description']}

Assume source is "data/input.csv" and destination is "data/destination.db" with table name "users" unless specified otherwise.
Return transformations as a dictionary, where key is column name and value is the operation (e.g. "uppercase").
"""
    try:
        config = structured_llm.invoke(prompt)
        if hasattr(config, "model_dump"):
            config_dict = config.model_dump()
        else:
            config_dict = dict(config)
            
        logs.append("Planner: Successfully planned execution.")
        return {"config": config_dict, "status": "planned", "logs": logs, "errors": errors, "retry_count": state.get("retry_count", 0)}
    except Exception as e:
        err_msg = f"Planner failed: {str(e)}"
        errors.append(err_msg)
        logs.append(err_msg)
        return {"status": "failed", "logs": logs, "errors": errors}

# 2. Validator Agent
def validator_agent(state: PipelineState):
    logs = state.get("logs", []) or []
    errors = state.get("errors", []) or []
    config = state.get("config", {})
    
    logs.append("Validator: Checking configuration...")
    
    # Check source
    source_path = config.get("source_path", "")
    if not os.path.exists(source_path):
        err = f"Validation failed: Source file '{source_path}' does not exist locally."
        errors.append(err)
        logs.append(err)
        return {"status": "validation_failed", "logs": logs, "errors": errors}
        
    logs.append("Validator: Validation passed. Awaiting execution approval.")
    # State pauses after this node because we compile with interrupt_before="executor_agent"
    return {"status": "waiting_approval", "logs": logs}

# 3. Executor Agent
def executor_agent(state: PipelineState):
    logs = state.get("logs", []) or []
    config = state.get("config", {})
    current_data = state.get("current_data", []) or []
    
    logs.append("Executor: Triggering Extract Phase...")
    
    EXTRACTOR_URL = os.getenv("EXTRACTOR_URL", "http://localhost:8001")
    TRANSFORMER_URL = os.getenv("TRANSFORMER_URL", "http://localhost:8002")
    LOADER_URL = os.getenv("LOADER_URL", "http://localhost:8003")
    
    try:
        # Extract
        resp = httpx.post(f"{EXTRACTOR_URL}/extract", json={"source_path": config["source_path"]}, timeout=30.0)
        resp.raise_for_status()
        current_data = resp.json().get("data", [])
        
        # Transform
        logs.append("Executor: Triggering Transform Phase...")
        resp = httpx.post(f"{TRANSFORMER_URL}/transform", json={
            "data": current_data,
            "transformations": config.get("transformations", {})
        }, timeout=30.0)
        resp.raise_for_status()
        current_data = resp.json().get("data", [])
        
        # Load
        logs.append("Executor: Triggering Load Phase...")
        resp = httpx.post(f"{LOADER_URL}/load", json={
            "data": current_data,
            "destination": config["destination_path"],
            "table_name": config["table_name"]
        }, timeout=30.0)
        resp.raise_for_status()
        
        logs.append("Executor: Pipeline completed successfully.")
        return {"status": "completed", "current_data": [], "logs": logs}
        
    except httpx.HTTPError as e:
        err = f"Executor ran into HTTP Exception: {str(e)}"
        logs.append(err)
        return {"status": "execution_failed", "logs": logs, "current_data": current_data}
    except Exception as e:
        err = f"Executor ran into Unknown Exception: {str(e)}"
        logs.append(err)
        return {"status": "execution_failed", "logs": logs, "current_data": current_data}

# 4. Monitor Agent
def monitor_agent(state: PipelineState):
    logs = state.get("logs", []) or []
    errors = state.get("errors", []) or []
    retry_count = state.get("retry_count", 0)
    
    logs.append(f"Monitor: Analyzing failure. Current Retry Count: {retry_count}")
    
    EXTRACTOR_URL = os.getenv("EXTRACTOR_URL", "http://localhost:8001")
    TRANSFORMER_URL = os.getenv("TRANSFORMER_URL", "http://localhost:8002")
    LOADER_URL = os.getenv("LOADER_URL", "http://localhost:8003")
    
    # Poll health of services to see if it's transient
    services = [
        ("Extractor", f"{EXTRACTOR_URL}/health"),
        ("Transformer", f"{TRANSFORMER_URL}/health"),
        ("Loader", f"{LOADER_URL}/health")
    ]
    
    all_healthy = True
    for name, url in services:
        try:
            r = httpx.get(url, timeout=5.0)
            if r.status_code != 200:
                all_healthy = False
                logs.append(f"Monitor: {name} service is reporting unhealthy.")
        except Exception:
            all_healthy = False
            logs.append(f"Monitor: {name} service is UNREACHABLE.")
            
    if retry_count < 3:
        retry_count += 1
        logs.append(f"Monitor: Initiating retry {retry_count}/3.")
        return {"status": "retrying", "logs": logs, "retry_count": retry_count}
    else:
        err = "Monitor: Max retries reached. Failing pipeline entirely."
        logs.append(err)
        errors.append(err)
        return {"status": "failed", "logs": logs, "errors": errors, "retry_count": retry_count}

# Graph Definition
builder = StateGraph(PipelineState)

builder.add_node("planner_agent", planner_agent)
builder.add_node("validator_agent", validator_agent)
builder.add_node("executor_agent", executor_agent)
builder.add_node("monitor_agent", monitor_agent)

builder.add_edge(START, "planner_agent")

def route_planner(state: PipelineState):
    if state.get("status") == "failed":
        return END
    return "validator_agent"

builder.add_conditional_edges("planner_agent", route_planner)

def route_validator(state: PipelineState):
    if state.get("status") == "validation_failed":
        return END
    return "executor_agent"

builder.add_conditional_edges("validator_agent", route_validator)

def route_executor(state: PipelineState):
    if state.get("status") == "execution_failed":
        return "monitor_agent"
    return END

builder.add_conditional_edges("executor_agent", route_executor)

def route_monitor(state: PipelineState):
    if state.get("status") == "retrying":
        return "executor_agent"
    return END

builder.add_conditional_edges("monitor_agent", route_monitor)

# Graph compilation is injected with checkpointer in the api/main.py
