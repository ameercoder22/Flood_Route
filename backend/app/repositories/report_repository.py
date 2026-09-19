from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.schemas.report import StoredReport

logger = logging.getLogger(__name__)


class DatabaseError(RuntimeError):
    pass


class ReportRepository(ABC):
    @abstractmethod
    def create_report(self, report: StoredReport) -> None: raise NotImplementedError

    @abstractmethod
    def get_report(self, report_id: str) -> StoredReport | None: raise NotImplementedError

    @abstractmethod
    def list_active_reports(self) -> list[StoredReport]: raise NotImplementedError


class DynamoDBReportRepository(ReportRepository):
    def __init__(self, region: str, table_name: str):
        if not region or not table_name:
            raise ValueError("AWS_REGION and DYNAMODB_TABLE_NAME are required for DynamoDB")
        dynamodb = boto3.resource("dynamodb", region_name=region, config=Config(connect_timeout=10, read_timeout=20))
        self.table = dynamodb.Table(table_name)

    @staticmethod
    def _serialize(report: StoredReport) -> dict[str, Any]:
        data = report.model_dump(mode="json")
        for key in ("text_analysis", "image_analysis", "final_analysis"):
            if data.get(key) is None:
                data.pop(key, None)
        return data

    def create_report(self, report: StoredReport) -> None:
        try:
            self.table.put_item(Item=self._serialize(report))
        except (ClientError, BotoCoreError, Exception) as exc:
            logger.exception("DynamoDB create failed for %s", report.report_id)
            raise DatabaseError("Could not store flood report") from exc

    def get_report(self, report_id: str) -> StoredReport | None:
        try:
            response = self.table.get_item(Key={"report_id": report_id})
        except (ClientError, BotoCoreError, Exception) as exc:
            logger.exception("DynamoDB get failed for %s", report_id)
            raise DatabaseError("Could not retrieve flood report") from exc
        item = response.get("Item")
        return StoredReport.model_validate(item) if item else None

    def list_active_reports(self) -> list[StoredReport]:
        try:
            items: list[dict[str, Any]] = []
            response = self.table.scan(
                FilterExpression="#status = :active",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":active": "ACTIVE"},
            )
            items.extend(response.get("Items", []))
            while response.get("LastEvaluatedKey"):
                response = self.table.scan(
                    FilterExpression="#status = :active",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={":active": "ACTIVE"},
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(response.get("Items", []))
            return [StoredReport.model_validate(item) for item in items]
        except (ClientError, BotoCoreError, Exception) as exc:
            logger.exception("DynamoDB active-report scan failed")
            raise DatabaseError("Could not list active flood reports") from exc


class InMemoryReportRepository(ReportRepository):
    def __init__(self):
        self._items: dict[str, StoredReport] = {}

    def create_report(self, report: StoredReport) -> None:
        self._items[report.report_id] = report

    def get_report(self, report_id: str) -> StoredReport | None:
        return self._items.get(report_id)

    def list_active_reports(self) -> list[StoredReport]:
        return [item for item in self._items.values() if item.status.value == "ACTIVE"]
