from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import os

app = FastAPI(title="Extractor Service")

class ExtractRequest(BaseModel):
    source_path: str

@app.post("/extract")
async def extract_data(request: ExtractRequest):
    if not os.path.exists(request.source_path):
        raise HTTPException(status_code=404, detail=f"Source file not found: {request.source_path}")
    
    try:
        df = pd.read_csv(request.source_path)
        # Assuming returning JSON orient='records'
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
