from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from ..storage import assert_schema_version, connect_read_only


class DashboardRepository:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path).resolve()
        if not self.database_path.is_file():
            raise FileNotFoundError(
                f"Dashboard database not found: {self.database_path}; run `retail-rfm build` first"
            )
        assert_schema_version(self.database_path)
        with connect_read_only(self.database_path) as connection:
            self.customers = pd.read_sql_query(
                "SELECT * FROM customer_segments ORDER BY customer_id", connection
            )
            self.profiles = pd.read_sql_query(
                "SELECT * FROM segment_profiles ORDER BY segment_order", connection
            )
            self.centroids = pd.read_sql_query(
                "SELECT * FROM cluster_centroids ORDER BY segment_code", connection
            )
            self.countries = pd.read_sql_query(
                "SELECT * FROM customer_countries ORDER BY customer_id, country", connection
            )
            self.evidence = pd.read_sql_query(
                "SELECT * FROM model_evidence ORDER BY evidence_type, candidate, k, metric_name",
                connection,
            )
            self.metadata = dict(
                connection.execute(
                    "SELECT metadata_key, metadata_value FROM model_metadata ORDER BY metadata_key"
                ).fetchall()
            )
        self._country_customers = {
            country: set(group["customer_id"].astype(str))
            for country, group in self.countries.groupby("country")
        }
        self.customer_options = [
            {
                "label": f"{row.customer_id} · {row.segment_code} · {row.country_display}",
                "value": str(row.customer_id),
            }
            for row in self.customers.itertuples()
        ]

    @property
    def country_options(self) -> list[dict[str, str]]:
        return [
            {"label": country, "value": country}
            for country in sorted(self._country_customers, key=lambda value: (value != "United Kingdom", value))
        ]

    def filtered_customers(
        self,
        segments: list[str] | None,
        countries: list[str] | None,
        cap_status: str,
    ) -> pd.DataFrame:
        frame = self.customers
        if segments:
            frame = frame.loc[frame["segment_code"].isin(segments)]
        if countries:
            eligible: set[str] = set()
            for country in countries:
                eligible.update(self._country_customers.get(country, set()))
            frame = frame.loc[frame["customer_id"].astype(str).isin(eligible)]
        if cap_status == "capped":
            frame = frame.loc[frame["any_capped_flag"].eq(1)]
        elif cap_status == "uncapped":
            frame = frame.loc[frame["any_capped_flag"].eq(0)]
        return frame.copy()

    def customer(self, customer_id: str) -> pd.Series:
        selected = self.customers.loc[self.customers["customer_id"].astype(str).eq(str(customer_id))]
        if selected.empty:
            raise KeyError(f"Unknown CustomerID: {customer_id}")
        return selected.iloc[0]

    def profile(self, segment_code: str) -> pd.Series:
        return self.profiles.loc[self.profiles["segment_code"].eq(segment_code)].iloc[0]

    @lru_cache(maxsize=256)
    def timeline(self, customer_id: str) -> pd.DataFrame:
        with connect_read_only(self.database_path) as connection:
            return pd.read_sql_query(
                """
                SELECT customer_id, invoice_no, invoice_date, invoice_amount,
                       line_count, is_cancellation, has_valid_positive_line
                FROM customer_invoice_timeline
                WHERE customer_id = ?
                ORDER BY invoice_date, invoice_no
                """,
                connection,
                params=(str(customer_id),),
                parse_dates=["invoice_date"],
            )

    def representative_ids(self) -> dict[str, str]:
        return (
            self.customers.loc[self.customers["is_representative"].eq(1)]
            .set_index("segment_code")["customer_id"]
            .astype(str)
            .sort_index()
            .to_dict()
        )
