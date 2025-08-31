from fastapi import FastAPI, File, UploadFile, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import APIRouter
import pandas as pd
import io
from services.dataset import DatasetManager
from typing import List

dataset_router = APIRouter()

dataset_manager = DatasetManager()

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename: str) -> bool:
    """Vérifier si l'extension du fichier est autorisée"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@dataset_router.get("/datasets/")
async def list_datasets():
    """GET /datasets/ - List all uploaded datasets"""
    try:
        datasets = dataset_manager.list_datasets()
        return [dataset.to_dict() for dataset in datasets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@dataset_router.post("/datasets/")
async def create_dataset(file: UploadFile = File(...)):
    """POST /datasets/ - create a dataset from a csv file"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file was uploaded")
        
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail="Only csv files are accepted"
            )
        
        content = await file.read()
        file_size = len(content)
        try:
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"corrupted file: {str(e)}"
            )
        
        dataset = dataset_manager.create_dataset(
            original_filename=file.filename,
            file_size=file_size,
            df=df
        )
        
        return {
            'id': dataset.id,
            'message': 'Dataset create with success',
            'dataset': dataset.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
