"""Land the bronze Parquet files in the lake.

    python ingest.py                 # every table under data/bronze/
    python ingest.py gl_journal      # one table

Regenerate the source files first with generate_data.py.
"""
import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

BUCKET = os.environ["LAKE_BUCKET"]
BRONZE = ROOT / "data" / "bronze"


def s3():
    return boto3.client("s3", endpoint_url=os.environ["AWS_ENDPOINT_URL"])


def ensure_bucket(client):
    # head_bucket, not list_buckets: a bucket-scoped token (R2/S3 best practice) can't list.
    try:
        client.head_bucket(Bucket=BUCKET)
    except client.exceptions.ClientError as e:
        if e.response["Error"]["Code"] not in ("404", "NoSuchBucket"):
            raise
        client.create_bucket(Bucket=BUCKET)


def main(tables=None):
    if not BRONZE.exists():
        raise SystemExit("data/bronze is empty; run generate_data.py first")
    client = s3()
    ensure_bucket(client)
    dirs = [BRONZE / t for t in tables] if tables else sorted(p for p in BRONZE.iterdir() if p.is_dir())
    for d in dirs:
        for f in sorted(d.glob("*.parquet")):
            key = f"bronze/{d.name}/{f.name}"
            client.upload_file(str(f), BUCKET, key)
            print(f"s3://{BUCKET}/{key}  ({f.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
