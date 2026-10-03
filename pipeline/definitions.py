"""Dagster definitions: generate -> land in lake -> dbt (silver + gold).

Run:  run-dagster.cmd   then open http://localhost:3000
"""
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from dagster import AssetExecutionContext, AssetKey, AssetSpec, Definitions, MaterializeResult, asset, multi_asset
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

import ingest  # noqa: E402  (ROOT is on sys.path via run-dagster.cmd)

BRONZE_TABLES = [
    "regions", "hubs", "suppliers", "components", "server_skus", "bom",
    "purchase_orders", "inventory_snapshots", "capacity_forecast", "rack_deployments",
    "supplier_invoices", "cost_centers", "gl_accounts", "gl_journal", "budget",
]

dbt_project = DbtProject(project_dir=ROOT / "lakehouse", profiles_dir=ROOT / "lakehouse")
dbt_project.prepare_if_dev()


class LakeTranslator(DagsterDbtTranslator):
    """dbt source `bronze.<table>` is the Dagster asset `bronze/<table>` produced by bronze_lake."""

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        if dbt_resource_props["resource_type"] == "source":
            return AssetKey(["bronze", dbt_resource_props["name"]])
        return super().get_asset_key(dbt_resource_props)


@asset(group_name="bronze")
def source_files(context: AssetExecutionContext) -> None:
    """Regenerate the Meridian Cloud source extracts (data/bronze/*.parquet)."""
    out = subprocess.run([sys.executable, str(ROOT / "generate_data.py")], capture_output=True, text=True, check=True)
    context.log.info(out.stdout)


@multi_asset(
    specs=[AssetSpec(["bronze", t], deps=[source_files], group_name="bronze") for t in BRONZE_TABLES],
)
def bronze_lake(context: AssetExecutionContext):
    """Land every source extract in s3://<bucket>/bronze/<table>/."""
    ingest.main()
    for t in BRONZE_TABLES:
        yield MaterializeResult(asset_key=["bronze", t])


@dbt_assets(manifest=dbt_project.manifest_path, dagster_dbt_translator=LakeTranslator())
def lakehouse_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


defs = Definitions(
    assets=[source_files, bronze_lake, lakehouse_dbt_assets],
    resources={
        "dbt": DbtCliResource(
            project_dir=dbt_project,
            # The venv's dbt, so this works without activating the venv or touching PATH.
            dbt_executable=str(Path(sys.executable).with_name("dbt.exe")),
        )
    },
)
