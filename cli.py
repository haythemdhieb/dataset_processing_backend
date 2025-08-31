#!/usr/bin/env python3
import argparse
import requests
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


API_BASE = "http://localhost:8000/dataset"


def list_datasets():
    resp = requests.get(f"{API_BASE}/datasets/")
    resp.raise_for_status()
    datasets = resp.json().get("datasets", [])
    if not datasets:
        logger.info("No datasets found.")
        return
    for ds in datasets:
        logger.info(f"{ds['id']}: {ds['filename']} ({ds['file_size']} bytes)")


def upload_dataset(file_path):
    if not os.path.exists(file_path):
        logger.info(f"File {file_path} does not exist.")
        return
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        resp = requests.post(f"{API_BASE}/datasets/", files=files)
        resp.raise_for_status()
        result = resp.json()
        logger.info(f"Dataset created: {result['dataset']['filename']} (id: {result['id']})")


def get_dataset(dataset_id):
    resp = requests.get(f"{API_BASE}/datasets/{dataset_id}/")
    if resp.status_code == 404:
        logger.info("Dataset not found.")
        return
    resp.raise_for_status()
    ds = resp.json()
    logger.info(f"{dataset_id}: {ds}")


def delete_dataset(dataset_id):
    resp = requests.delete(f"{API_BASE}/datasets/{dataset_id}/")
    if resp.status_code == 404:
        logger.info("Dataset not found.")
        return
    resp.raise_for_status()
    logger.info("Dataset deleted successfully.")


def export_excel(dataset_id, output_file):
    resp = requests.get(f"{API_BASE}/datasets/{dataset_id}/excel/")
    if resp.status_code == 404:
        logger.info("Dataset not found.")
        return
    resp.raise_for_status()
    with open(output_file, "wb") as f:
        f.write(resp.content)
    logger.info(f"Excel file saved to {output_file}")


def generate_plot(dataset_id, output_file):
    resp = requests.get(f"{API_BASE}/datasets/{dataset_id}/plot/")
    if resp.status_code == 404:
        logger.info("Dataset not found.")
        return
    resp.raise_for_status()
    with open(output_file, "wb") as f:
        f.write(resp.content)
    logger.info(f"Plot PDF saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Dataset CLI client")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List all datasets")

    upload_parser = subparsers.add_parser("upload", help="Upload a CSV dataset")
    upload_parser.add_argument("file", help="Path to CSV file")

    get_parser = subparsers.add_parser("get", help="Retrieve a dataset info")
    get_parser.add_argument("id", help="Dataset ID")

    delete_parser = subparsers.add_parser("delete", help="Delete a dataset")
    delete_parser.add_argument("id", help="Dataset ID")

    excel_parser = subparsers.add_parser("excel", help="Export dataset to Excel")
    excel_parser.add_argument("id", help="Dataset ID")
    excel_parser.add_argument("output", help="Output Excel filename")

    plot_parser = subparsers.add_parser("plot", help="Generate PDF plots for dataset")
    plot_parser.add_argument("id", help="Dataset ID")
    plot_parser.add_argument("output", help="Output PDF filename")

    args = parser.parse_args()

    try:
        if args.command == "list":
            list_datasets()
        elif args.command == "upload":
            upload_dataset(args.file)
        elif args.command == "get":
            get_dataset(args.id)
        elif args.command == "delete":
            delete_dataset(args.id)
        elif args.command == "excel":
            export_excel(args.id, args.output)
        elif args.command == "plot":
            generate_plot(args.id, args.output)
        else:
            parser.print_help()
    except requests.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
