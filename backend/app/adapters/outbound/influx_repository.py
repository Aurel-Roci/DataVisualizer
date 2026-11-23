import logging
from datetime import datetime, timedelta

from influxdb_client_3 import InfluxDBClient3

from ...config.settings import get_settings
from ...domain.errors import StorageUnavailable
from ...domain.models import BloodworkRecord

logger = logging.getLogger(__name__)


class InfluxBloodworkRepository:
    """BloodworkRepository port implementation backed by InfluxDB v3"""

    def __init__(self, host: str | None = None, token: str | None = None, database: str | None = None):
        """
        Initialize InfluxDB v3 client

        Args:
            host: InfluxDB host URL
            token: Authentication token
            database: Database name (defaults to INFLUXDB_DATABASE, then "bloodwork")
        """
        settings = get_settings()
        self.host = host or settings.influxdb_host
        self.token = token or settings.influxdb_token
        self.database = database or settings.influxdb_database

        if not self.host or not self.token:
            raise ValueError("InfluxDB host and token must be provided")

        self.client = InfluxDBClient3(host=self.host, token=self.token, database=self.database)

    def store(self, record: BloodworkRecord) -> None:
        """
        Store a complete bloodwork record in InfluxDB

        Args:
            record: BloodworkRecord object

        Raises:
            StorageUnavailable: if the write fails
        """
        try:
            # Prepare data points for batch write
            points = []
            for result in record.results:
                fields: dict[str, float | str] = {"value": float(result.value)}
                # Free-text and high cardinality, so a field rather than a tag
                if result.reference_range:
                    fields["reference_range"] = result.reference_range

                point = {
                    "measurement": "bloodwork",
                    "tags": {
                        "patient_name": record.patient_name,
                        "test_name": result.test_name,
                        "unit": result.unit,
                    },
                    "fields": fields,
                    "time": record.test_date,
                }

                points.append(point)

            self.client.write(points)

        except Exception as e:
            logger.exception(f"Error storing bloodwork record: {e}")
            raise StorageUnavailable("Failed to store results in database") from e

    def query(self, start_date: datetime, end_date: datetime, test_names: list[str] | None = None) -> list[dict]:
        """
        Query bloodwork rows (end_date is inclusive of the whole day), newest first

        Args:
            start_date: Start date for query range
            end_date: End date for query range
            test_names: List of specific tests to query

        Returns:
            list[dict]: One JSON-safe dict per stored point (missing values are None)

        Raises:
            StorageUnavailable: if the query fails
        """
        try:
            query = """
                SELECT *
                FROM "bloodwork"
                WHERE time >= $start_date
                AND time < $end_date
            """
            params = {
                "start_date": str(start_date.date()),
                "end_date": str(end_date.date() + timedelta(days=1)),  # exclusive upper bound
            }

            if test_names:
                placeholders = []
                for i, name in enumerate(test_names):
                    params[f"test_name_{i}"] = name
                    placeholders.append(f"$test_name_{i}")
                query += f" AND test_name IN ({', '.join(placeholders)})"

            query += " ORDER BY time DESC"

            df = self.client.query(query, query_parameters=params).to_pandas()
            # pandas 3 fills missing strings with NaN (not None), which is not JSON serializable
            return df.astype(object).where(df.notna(), None).to_dict("records")

        except Exception as e:
            logger.exception(f"Error querying patient tests: {e}")
            raise StorageUnavailable("Failed to fetch results") from e

    def close(self):
        """Close the database connection"""
        if hasattr(self.client, "close"):
            self.client.close()
