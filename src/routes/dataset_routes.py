from fastapi import File, Response, UploadFile, HTTPException
from fastapi import APIRouter
import pandas as pd
import io
from services.dataset import DatasetManager
from typing import List
from utils.helpers import allowed_file

dataset_router = APIRouter()

dataset_manager = DatasetManager()


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

@dataset_router.get("/datasets/{dataset_id}/")
async def get_dataset(dataset_id: str):
    """GET /datasets/<id>/ - Retrieve a specific dataset"""
    try:
        dataset = dataset_manager.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        return dataset.to_summary_dict()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@dataset_router.delete("/datasets/{dataset_id}/")
async def delete_dataset(dataset_id: str):
    """DELETE /datasets/<id>/ - Delete dataset"""
    try:
        if not dataset_manager.get_dataset(dataset_id):
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        success = dataset_manager.delete_dataset(dataset_id)
        if not success:
            raise HTTPException(status_code=500, detail="Error while deleting dataset")
        
        return {'message': 'dataset deleted'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@dataset_router.get("/datasets/{dataset_id}/excel/")
async def export_excel(dataset_id: str):
    """GET /datasets/<id>/excel/ - Exporter dataset in Excel fromat"""
    try:
        dataset = dataset_manager.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        df = dataset.get_dataframe()
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        
        output.seek(0)
        
        excel_filename = f"{dataset.filename.rsplit('.', 1)[0]}.xlsx"
        
        return Response(
            content=output.getvalue(),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": f"attachment; filename={excel_filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
