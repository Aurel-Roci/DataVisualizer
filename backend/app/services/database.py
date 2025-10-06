import logging

from influxdb_client_3 import InfluxDBClient3
from datetime import datetime
from typing import List, Optional
import os
import pandas as pd

from ..models.bloodwork_metadata import BloodworkRecord

logger = logging.getLogger(__name__)

class InfluxDBService:
    """Service class for InfluxDB v3 operations"""

    def __init__(self,
                 host: str = None,
                 token: str = None,
                 database: str = "bloodwork"):
        """
        Initialize InfluxDB v3 client

        Args:
            host: InfluxDB host URL
            token: Authentication token
            database: Database name
        """
        self.host = host or os.getenv("INFLUXDB_HOST")
        self.token = token or os.getenv("INFLUXDB_TOKEN")
        self.database = database

        if not self.host or not self.token:
            raise ValueError("InfluxDB host and token must be provided")

        self.client = InfluxDBClient3(
            host=self.host,
            token=self.token,
            database=self.database
        )

    def store_bloodwork_record(self, record: BloodworkRecord) -> bool:
        """
        Store a complete bloodwork record in InfluxDB

        Args:
            record: BloodworkRecord object

        Returns:
            bool: Success status
        """
        try:
            # Prepare data points for batch write
            points = []
            for result in record.results:
                point = {
                    "measurement": "bloodwork",
                    "tags": {
                        "patient_name": record.patient_name,
                        "test_name": result.test_name,
                        "unit": result.unit,
                    },
                    "fields": {
                        "value": float(result.value)
                    },
                    "time": record.test_date
                }

                # Add optional tags
                if result.reference_range:
                    point["tags"]["reference_range"] = result.reference_range

                points.append(point)

            self.client.write(points)
            return True

        except Exception as e:
            logging.exception(f"Error storing bloodwork record {e}")
            return False

    def get_patient_tests(self,
                          start_date: datetime,
                          end_date: datetime,
                          test_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Query bloodwork data

        Args:
            start_date: Start date for query range
            end_date: End date for query range
            test_names: List of specific tests to query

        Returns:
            pandas.DataFrame: Query results
        """
        try:
            query = f'''
                SELECT *
                FROM "bloodwork"
                WHERE time >= '{start_date.date()}'
                AND time <= '{end_date.date()}'
            '''

            if test_names:
                test_filter = "', '".join(test_names)
                query += f" AND test_name IN ('{test_filter}')"

            query += " ORDER BY time DESC"

            result = self.client.query(query)
            return result.to_pandas()

        except Exception as e:
            logger.exception(f"Error querying patient tests: {e}")
            return pd.DataFrame()

    def get_test_history(self,
                         test_name: str,
                         limit: int = 1000) -> pd.DataFrame:
        """
        Get historical values for a specific test

        Args:
            test_name: Name of the test value
            limit: Maximum number of records

        Returns:
            pandas.DataFrame: Historical test values
        """
        try:
            query = f'''
                SELECT *
                FROM "bloodwork"
                AND test_name = '{test_name}'
                ORDER BY time DESC
                LIMIT {limit}
            '''

            result = self.client.query(query)
            return result.to_pandas()

        except Exception as e:
            logger.exception(f"Error querying test history: {e}")
            return pd.DataFrame()

    def delete_date_data(self, date: str) -> bool:
        """
        Delete all data for a specific date

        Args:
            date: Date of data to delete

        Returns:
            bool: Success status
        """
        try:
            query = f'''
                DELETE FROM "bloodwork"
                WHERE time = '{date}'
            '''

            self.client.query(query)
            return True

        except Exception as e:
            logger.exception(f"Error deleting patient data: {e}")
            return False

    def close(self):
        """Close the database connection"""
        if hasattr(self.client, 'close'):
            self.client.close()
