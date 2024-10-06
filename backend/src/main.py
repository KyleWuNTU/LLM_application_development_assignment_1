import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .document_processor import DocumentProcessor
import os
from pydantic import BaseModel
from .state_manager import StateManager

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

state_manager = StateManager(UPLOAD_DIR)

class QueryRequest(BaseModel):
    question: str
    documents: list[str] = []

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "This is the backend for the RAG application"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"Received file upload request for {file.filename}")
    try:
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)
        
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        contents = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        process_result = state_manager.process_document(file_path)
        
        if process_result is None:
            raise ValueError(f"Failed to process file {file.filename}")
        
        logger.info(f"File {file.filename} processed successfully")
        return {
            "filename": process_result["file_name"],
            "status": "processed",
            "num_chunks": process_result["num_chunks"],
            "vector_store_size": process_result["vector_store_size"]
        }
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file {file.filename}: {str(e)}")

@app.post("/query")
async def query_document(request: QueryRequest):
    logger.info(f"Received query: {request.question}")
    try:
        response = state_manager.query(request.question)
        logger.info("Query processed successfully")
        return {"response": response}
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))