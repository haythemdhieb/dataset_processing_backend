import re
import io
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from fastapi import APIRouter, HTTPException, Response, UploadFile, File
from typing import List
from services.dataset import DatasetManager
from utils.helpers import allowed_file

dataset_router = APIRouter()
dataset_manager = DatasetManager()


@dataset_router.get("/datasets/", status_code=200)
async def list_datasets():
    """List all uploaded datasets"""
    try:
        datasets = dataset_manager.list_datasets()
        return {"datasets": [dataset.to_dict() for dataset in datasets]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")


@dataset_router.post("/datasets/", status_code=201)
async def create_dataset(file: UploadFile = File(...)):
    """Create a dataset from a CSV file"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Only CSV files are accepted")

        content = await file.read()
        file_size = len(content)
        try:
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV file: {str(e)}")

        dataset = dataset_manager.create_dataset(
            original_filename=file.filename,
            file_size=file_size,
            df=df
        )

        return {
            "id": dataset.id,
            "message": "Dataset created successfully",
            "dataset": dataset.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dataset: {str(e)}")


@dataset_router.get("/datasets/{dataset_id}/", status_code=200)
async def get_dataset(dataset_id: str):
    """Retrieve a specific dataset"""
    try:
        dataset = dataset_manager.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        return dataset.to_summary_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dataset: {str(e)}")


@dataset_router.delete("/datasets/{dataset_id}/", status_code=200)
async def delete_dataset(dataset_id: str):
    """Delete a dataset"""
    try:
        dataset = dataset_manager.get_dataset(dataset_id)
        print(dataset.to_dict())
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        success = dataset_manager.delete_dataset(dataset_id)
        if not success:
            raise HTTPException(status_code=500, detail="Error deleting dataset")

        return {"message": "Dataset deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete dataset: {str(e)}")


@dataset_router.get("/datasets/{dataset_id}/excel/", status_code=200)
async def export_excel(dataset_id: str):
    """Export dataset as Excel"""
    try:
        dataset = dataset_manager.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        df = dataset.get_dataframe()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')

        output.seek(0)
        excel_filename = re.sub(r"[^\w\-_. ]", "_", dataset.filename.rsplit(".", 1)[0]) + ".xlsx"

        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={excel_filename}"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export Excel: {str(e)}")


@dataset_router.get("/datasets/{dataset_id}/stats/", status_code=200)
async def get_stats(dataset_id: str):
    """Return statistics of a dataset"""
    try:
        dataset = dataset_manager.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        df = dataset.get_dataframe()
        stats = df.describe(include='all')
        stats_dict = {
            col: {idx: (None if pd.isna(stats.loc[idx, col]) 
                        else stats.loc[idx, col].item() if hasattr(stats.loc[idx, col], 'item') 
                        else stats.loc[idx, col])
                  for idx in stats.index}
            for col in stats.columns
        }

        additional_info = {
            "shape": list(df.shape),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "null_counts": {col: int(count) for col, count in df.isnull().sum().items()},
            "memory_usage": {col: int(usage) for col, usage in df.memory_usage(deep=True).items()}
        }

        return {"describe": stats_dict, "additional_info": additional_info}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dataset statistics: {str(e)}")


@dataset_router.get("/datasets/{dataset_id}/plot/", status_code=200)
async def generate_plot(dataset_id: str):
    """Generate a PDF with histograms for numeric columns"""
    try:
        dataset = dataset_manager.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        df = dataset.get_dataframe()
        numerical_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
        if not numerical_cols:
            raise HTTPException(status_code=400, detail="No numeric columns found in dataset")

        output = io.BytesIO()
        with PdfPages(output) as pdf:
            n_cols = min(3, len(numerical_cols))
            n_rows = (len(numerical_cols) + n_cols - 1) // n_cols

            fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 5 * n_rows))
            axes = axes.flatten() if len(numerical_cols) > 1 else [axes]

            for i, col in enumerate(numerical_cols):
                ax = axes[i]
                df[col].hist(bins=30, ax=ax, alpha=0.7)
                ax.set_title(f'Histogram of {col}')
                ax.set_xlabel(col)
                ax.set_ylabel('Frequency')
                ax.grid(True, alpha=0.3)

            for j in range(len(numerical_cols), len(axes)):
                axes[j].set_visible(False)

            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

        output.seek(0)
        plot_filename = re.sub(r"[^\w\-_. ]", "_", dataset.filename.rsplit(".", 1)[0]) + "_plots.pdf"

        return Response(
            content=output.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={plot_filename}"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate plots: {str(e)}")
