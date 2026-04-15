from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import sqlite3
import os

app = FastAPI(title="Loader Service")

class LoadRequest(BaseModel):
    data: List[Dict[str, Any]]
    destination: str
    table_name: str

@app.post("/load")
async def load_data(request: LoadRequest):
    try:
        df = pd.DataFrame(request.data)
        
        # Create directory if doesn't exist
        dest_dir = os.path.dirname(request.destination)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        
        conn = sqlite3.connect(request.destination)
        df.to_sql(request.table_name, conn, if_exists="replace", index=False)
        conn.close()
        
        return {"status": "success", "rows_loaded": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
