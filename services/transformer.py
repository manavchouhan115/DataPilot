from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd

app = FastAPI(title="Transformer Service")

class TransformRequest(BaseModel):
    data: List[Dict[str, Any]]
    transformations: Dict[str, str] = {} # e.g. {"name": "uppercase"}

@app.post("/transform")
async def transform_data(request: TransformRequest):
    try:
        df = pd.DataFrame(request.data)
        
        # Simple transformations based on instruction
        for col, op in request.transformations.items():
            if col in df.columns:
                if op == "uppercase":
                    df[col] = df[col].astype(str).str.upper()
                elif op == "lowercase":
                    df[col] = df[col].astype(str).str.lower()
        
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
