"""Saga orchestrator tests — mocked HTTP calls and DB connection."""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from worker.sagas import DeviceRetirementSaga

TENANT = uuid4()
DEVICE_ID = str(uuid4())
USER_ID = str(uuid4())


def _mock_conn():
    """Create a mock AsyncConnection that records SQL calls."""
    conn = AsyncMock()
    conn.execute = AsyncMock()
    return conn


def _mock_httpx_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


class TestDeviceRetirementSaga:
    @pytest.mark.asyncio
    @patch("worker.sagas.httpx.AsyncClient")
    async def test_successful_saga(self, mock_client_cls):
        conn = _mock_conn()
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        # First call: resolve email
        mock_client.get.return_value = _mock_httpx_response(
            200, {"email": "user@example.com"}
        )
        # Second call: send email
        mock_client.post.return_value = _mock_httpx_response(200)

        saga = DeviceRetirementSaga(conn)
        await saga.start(
            tenant_id=TENANT,
            device_id=DEVICE_ID,
            user_id=USER_ID,
            reason="End of life",
        )

        # Verify saga_state was inserted
        insert_call = conn.execute.call_args_list[0]
        sql_text = str(insert_call[0][0])
        assert "INSERT INTO saga_state" in sql_text

        # Verify final status is "completed"
        last_update = conn.execute.call_args_list[-1]
        params = last_update[0][1]
        assert params["status"] == "completed"

    @pytest.mark.asyncio
    @patch("worker.sagas.httpx.AsyncClient")
    async def test_notify_failure_triggers_compensation(self, mock_client_cls):
        conn = _mock_conn()
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        # Email resolution fails
        mock_client.get.return_value = _mock_httpx_response(500)

        # Compensation call succeeds
        mock_client.post.return_value = _mock_httpx_response(200)

        saga = DeviceRetirementSaga(conn)
        await saga.start(
            tenant_id=TENANT,
            device_id=DEVICE_ID,
            user_id=USER_ID,
            reason="End of life",
        )

        # Verify compensation was attempted — status should be "compensated"
        statuses = [
            call[0][1]["status"]
            for call in conn.execute.call_args_list
            if isinstance(call[0][1], dict) and "status" in call[0][1]
        ]
        assert "compensating" in statuses
        assert "compensated" in statuses

    @pytest.mark.asyncio
    @patch("worker.sagas.httpx.AsyncClient")
    async def test_compensation_failure_results_in_failed(self, mock_client_cls):
        conn = _mock_conn()
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        # Email resolution fails
        mock_client.get.return_value = _mock_httpx_response(500)

        # Compensation also fails
        mock_client.post.side_effect = Exception("Network error")

        saga = DeviceRetirementSaga(conn)
        await saga.start(
            tenant_id=TENANT,
            device_id=DEVICE_ID,
            user_id=USER_ID,
            reason="End of life",
        )

        statuses = [
            call[0][1]["status"]
            for call in conn.execute.call_args_list
            if isinstance(call[0][1], dict) and "status" in call[0][1]
        ]
        assert "failed" in statuses
