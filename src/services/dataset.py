import os
import json
import uuid
import pickle
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class Dataset:
    """
    Represents a dataset and handles serialization, persistence, and DataFrame storage.
    """

    def __init__(
        self,
        id: str = None,
        filename: str = None,
        file_size: int = None,
        upload_date: datetime = None,
        data_path: str = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.filename = filename
        self.file_size = file_size
        self.upload_date = upload_date or datetime.utcnow()
        self.data_path = data_path

    def to_dict(self) -> Dict:
        """Convert the Dataset object to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size": self.file_size,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "data_path" : self.data_path
        }
    
    def to_summary_dict(self) -> dict:
        """
        Return only the fields needed for listing in the API:
        filename and file_size
        """
        return {
            "filename": self.filename,
            "file_size": self.file_size
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Dataset":
        """Create a Dataset object from a dictionary."""
        upload_date = None
        if data.get("upload_date"):
            upload_date = datetime.fromisoformat(data["upload_date"])

        return cls(
            id=data.get("id"),
            filename=data.get("filename"),
            file_size=data.get("file_size"),
            upload_date=upload_date,
            data_path=data.get("data_path"),
        )

    def get_dataframe(self) -> pd.DataFrame:
        """Store files in locally"""
        try:
            with open(self.data_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            raise Exception(f"Error while reading dataframe: {str(e)}")
    
    def save_dataframe(self, df: pd.DataFrame):
        """Save a pandas DataFrame to disk."""
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, "wb") as f:
                pickle.dump(df, f)
            logger.info(f"DataFrame saved successfully at {self.data_path}")
        except Exception as e:
            logger.error(f"Failed to save DataFrame for dataset {self.id}: {e}")
            raise

    def delete_files(self):
        """Supprimer les fichiers associés du disque"""
        try:
            if os.path.exists(self.data_path):
                os.remove(self.data_path)
        except Exception as e:
            logger.error(f"Error deleting files in {self.data_path}: {str(e)}")
    
class DatasetManager:
    """
    Manages CRUD operations for datasets using local storage and JSON-based metadata.
    """

    def __init__(self, storage_dir: str = "storage"):
        self.storage_dir = Path(storage_dir)
        self.metadata_file = self.storage_dir / "datasets_metadata.json"
        self.data_dir = self.storage_dir / "data"

        # Ensure required directories exist
        self.storage_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

        # Initialize metadata file if missing
        if not self.metadata_file.exists():
            self._save_metadata({})

    def _load_metadata(self) -> Dict:
        """Load dataset metadata from JSON."""
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Metadata file is corrupted: {e}")
            return {}
        except FileNotFoundError:
            logger.warning("Metadata file not found, initializing a new one.")
            return {}

    def _save_metadata(self, metadata: Dict):
        """Save dataset metadata to JSON."""
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info("Metadata updated successfully.")

    def create_dataset(self, original_filename: str, file_size: int, df: pd.DataFrame) -> Dataset:
        """Create and persist a new dataset."""
        dataset_id = str(uuid.uuid4())
        dataset = Dataset(
            id=dataset_id,
            filename=original_filename,
            file_size=file_size,
        )
        dataset.data_path = str(self.data_dir / f"{dataset.id}.pkl")
        dataset.save_dataframe(df)
        metadata = self._load_metadata()
        metadata[dataset.id] = dataset.to_dict()
        self._save_metadata(metadata)

        logger.info(f"Dataset {dataset.id} created successfully.")
        return dataset

    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Retrieve a dataset using ID"""
        metadata = self._load_metadata()
        if dataset_id not in metadata:
            return None
        
        dataset_data = metadata[dataset_id]
        dataset = Dataset.from_dict(dataset_data)
        return dataset

    def list_datasets(self) -> List[Dataset]:
        """Lister tous les datasets"""
        metadata = self._load_metadata()
        datasets = []
        
        for _, dataset_data in metadata.items():
            dataset = Dataset.from_dict(dataset_data)
            datasets.append(dataset)
        
        return datasets
    

    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset"""
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return False
        
        dataset.delete_files()
        metadata = self._load_metadata()
        if dataset_id in metadata:
            del metadata[dataset_id]
            self._save_metadata(metadata)
        
        return True