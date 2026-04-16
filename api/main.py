from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import os
from dotenv import load_dotenv

from langgraph.checkpoint.postgres import PostgresSaver

# Import builder from orchestrator
from agents.orchestrator import builder

load_dotenv()

app = FastAPI(title="DataPilot API Gateway")

# Connection pool for LangGraph Postgres Checkpointer
DB_URI = "postgresql://user:password@localhost:5432/langgraph_checkpoints"

# Initialize tables globally on startup
@app.on_event("startup")
def setup_database():
    try:
        import psycopg
        # Setup Checkpoints with autocommit True to avoid CREATE INDEX transaction errors
        with psycopg.connect(DB_URI, autocommit=True) as conn:
            checkpointer = PostgresSaver(conn)
            checkpointer.setup()
            print("Database setup complete.")
    except Exception as e:
        print(f"Failed to setup database: {e}")

class PipelineRequest(BaseModel):
    nl_description: str

def run_pipeline_task(pipeline_id: str, nl_description: str):
    """Run pipeline in background using Postgres Checkpointer."""
    try:
        with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
            graph = builder.compile(checkpointer=checkpointer, interrupt_before=["executor_agent"])
            
            config = {"configurable": {"thread_id": pipeline_id}}
            
            graph.invoke(
                {"nl_description": nl_description, "pipeline_id": pipeline_id},
                config
            )
    except Exception as e:
        print(f"Error running pipeline {pipeline_id}: {e}")

@app.post("/pipeline/{pipeline_id}/approve")
async def approve_pipeline(pipeline_id: str, background_tasks: BackgroundTasks):
    def resume_task(pid: str):
        try:
            with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
                graph = builder.compile(checkpointer=checkpointer, interrupt_before=["executor_agent"])
                config = {"configurable": {"thread_id": pid}}
                graph.invoke(None, config)
        except Exception as e:
            print(f"Error resuming pipeline {pid}: {e}")
            
    background_tasks.add_task(resume_task, pipeline_id)
    return {"message": "Pipeline approved and execution resumed", "pipeline_id": pipeline_id}

@app.post("/pipeline")
async def create_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    pipeline_id = str(uuid.uuid4())
    
    # Run graph asynchronously
    background_tasks.add_task(run_pipeline_task, pipeline_id, request.nl_description)
    
    return {"message": "Pipeline started", "pipeline_id": pipeline_id}

@app.get("/pipeline/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str):
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        config = {"configurable": {"thread_id": pipeline_id}}
        
        # Access state from checkpoint
        try:
            checkpoint_tuple = checkpointer.get_tuple(config)
            
            if not checkpoint_tuple:
                raise HTTPException(status_code=404, detail="Pipeline not found")
                
            state_values = checkpoint_tuple.checkpoint.get("channel_values", {})
            
            return {
                "pipeline_id": pipeline_id,
                "status": state_values.get("status", "unknown"),
                "error": state_values.get("error", None),
                "config": state_values.get("config", None)
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
