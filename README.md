# Dataset Management API and CLI Client

This project provides a **FastAPI backend** to manage CSV datasets and a **standalone Python CLI client** to interact with it. You can upload CSV files, list datasets, retrieve dataset info, delete datasets, export to Excel, and generate PDF plots of numeric columns.

---

## Features

- Upload CSV datasets
- List uploaded datasets
- Retrieve dataset details
- Delete datasets
- Export datasets to Excel
- Generate PDF plots for numeric columns

---

## Requirements

- Python 3.9+
- Install required Python packages:

```bash
pip install -r requirements.txt
```

## Running the FastAPI Backend

1. Navigate to the project root directory.
2. Start the server using `uvicorn`:

```bash
python src/app.py
```

The API will be available at `http://localhost:8000`.

---

## Using the CLI Client

The CLI client allows you to perform all API actions from the command line. Make sure the FastAPI server is running before using the CLI.

### Command Syntax

```bash
python cli.py <command> [arguments]
```

### Available Commands

- **List all datasets**

```bash
python cli.py list
```

- **Upload a CSV dataset**

```bash
python cli.py upload path/to/file.csv
```

- **Get dataset details**

```bash
python cli.py get <dataset_id>
```

- **Delete a dataset**

```bash
python cli.py delete <dataset_id>
```

- **Export dataset to Excel**

```bash
python cli.py excel <dataset_id> output.xlsx
```

- **Generate PDF plots for numeric columns**

```bash
python cli.py plot <dataset_id> output.pdf
```

> Replace `<dataset_id>` with the dataset ID returned when uploading a dataset.

---

## Project Structure

```
src/
│
├─ main.py              # FastAPI backend entrypoint
├─ services/
│   └─ dataset.py       # DatasetManager and dataset handling
├─ utils/
│   └─ helpers.py       # Helper functions (e.g., allowed_file)
├─ config/             # Configuration files

cli.py                # CLI client
requirements.txt      # Python dependencies
README.md 
```

---

## Notes

- CSV files are stored locally along with metadata in JSON format.
- Downloaded Excel and PDF files will be saved to the paths you provide in the CLI.
- The CLI is fully standalone and communicates with the backend via HTTP requests.
---

## Example Workflow

1. Start the FastAPI server:

```bash
uvicorn main:app --host 0.0.0.0 --port 7000 --reload
```

2. Upload a CSV dataset:

```bash
python cli.py upload data/sample.csv
```

3. List all datasets:

```bash
python cli.py list
```

4. Export the dataset to Excel:

```bash
python cli.py excel <dataset_id> exported.xlsx
```

5. Generate PDF plots:

```bash
python cli.py plot <dataset_id> plots.pdf
```

6. Delete a dataset:

```bash
python cli.py delete <dataset_id>
```
