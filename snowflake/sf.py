"""Shared Snowflake connection using key-pair auth and the values in .env."""
import os
from pathlib import Path

import snowflake.connector
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def connect(**overrides):
    missing = [k for k in ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER") if not os.getenv(k)]
    if missing:
        raise SystemExit(f"Fill these in .env first: {', '.join(missing)}")
    key_path = Path(os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", ROOT / "snowflake" / "rsa_key.p8"))
    key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    der = key.private_bytes(
        serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    params = dict(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        private_key=der,
        role=os.getenv("SNOWFLAKE_ROLE", "LAKE_DEV"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "LAKE_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "LAKE"),
    )
    params.update(overrides)
    return snowflake.connector.connect(**params)
