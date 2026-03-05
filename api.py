from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from analyser import BankStatementAnalyser
import uvicorn
import io

app = FastAPI(title="Bank Analyser API", description="API for detecting impulsive financial behaviour.")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the analyser once
# Using the default settings from the Python module
analyser = BankStatementAnalyser()

@app.post("/analyse")
async def analyse(statement: UploadFile = File(...)):
    """
    Accepts a Bank Statement file upload, parses the columns, runs the ML 
    feature engineering and ensemble model to calculate the Impulse Risk Score, 
    and returns a full JSON payload with Risk Profiles, Base64 Charts, and Nudges.
    """
    contents = await statement.read()
    
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")
        
    try:
        # Pass the bytes directly to analyser
        result = analyser.analyse(file_bytes=contents, filename=statement.filename)
        return result
    except ValueError as e:
        # ValueErrors typically come from analyser logic (e.g., unsupported format, validation failure)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal processing error: {str(e)}")

# Add a health check
@app.get("/")
def read_root():
    return {"status": "ok", "app": "bank_analyser_api"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
