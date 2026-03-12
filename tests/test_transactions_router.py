import io

from fastapi.testclient import TestClient

from tests.conftest import CHASE_CSV_CONTENT, CHASE_CSV_EMPTY, CHASE_CSV_MISSING_COLUMN

VALID_JSON_TRANSACTION = {
    "transaction_date": "2024-01-15",
    "amount": 45.99,
    "description": "AMAZON.COM",
    "category": "Shopping",
    "type": "debit",
    "account": "Chase Checking 1234",
    "owner": "alice",
}


def _csv_upload(client: TestClient, csv_content: str, bank: str = "chase") -> object:
    return client.post(
        "/api/v1/transactions/",
        files={"file": ("transactions.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        data={"bank": bank, "account": "Chase Checking 1234", "owner": "alice"},
    )


class TestPostMultipart:
    def test_upload_chase_success(self, client):
        response = _csv_upload(client, CHASE_CSV_CONTENT)
        assert response.status_code == 201
        body = response.json()
        assert body["count"] == 3
        assert len(body["transaction_ids"]) == 3

    def test_upload_unknown_bank(self, client):
        response = _csv_upload(client, CHASE_CSV_CONTENT, bank="foobank")
        assert response.status_code == 400

    def test_upload_non_csv_file(self, client):
        response = client.post(
            "/api/v1/transactions/",
            files={"file": ("transactions.txt", b"not a csv", "text/plain")},
            data={"bank": "chase", "account": "Acct", "owner": "alice"},
        )
        assert response.status_code == 400

    def test_upload_empty_csv(self, client):
        response = _csv_upload(client, CHASE_CSV_EMPTY)
        assert response.status_code == 201
        body = response.json()
        assert body["count"] == 0

    def test_upload_missing_column(self, client):
        response = _csv_upload(client, CHASE_CSV_MISSING_COLUMN)
        assert response.status_code == 400


class TestPostJson:
    def test_create_single_transaction(self, client):
        response = client.post("/api/v1/transactions/", json=VALID_JSON_TRANSACTION)
        assert response.status_code == 201
        body = response.json()
        assert body["description"] == "AMAZON.COM"
        assert body["type"] == "debit"
        assert "id" in body

    def test_invalid_type_value(self, client):
        payload = {**VALID_JSON_TRANSACTION, "type": "transfer"}
        response = client.post("/api/v1/transactions/", json=payload)
        assert response.status_code == 422

    def test_missing_required_field(self, client):
        payload = {k: v for k, v in VALID_JSON_TRANSACTION.items() if k != "amount"}
        response = client.post("/api/v1/transactions/", json=payload)
        assert response.status_code == 422


class TestListTransactions:
    def test_list_empty(self, client):
        response = client.get("/api/v1/transactions/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_after_upload(self, client):
        _csv_upload(client, CHASE_CSV_CONTENT)
        response = client.get("/api/v1/transactions/")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_filter_by_account(self, client):
        _csv_upload(client, CHASE_CSV_CONTENT)
        client.post(
            "/api/v1/transactions/",
            files={"file": ("t.csv", io.BytesIO(CHASE_CSV_CONTENT.encode("utf-8")), "text/csv")},
            data={"bank": "chase", "account": "Other Account", "owner": "bob"},
        )
        response = client.get("/api/v1/transactions/?account=Chase+Checking+1234")
        assert response.status_code == 200
        assert all(t["account"] == "Chase Checking 1234" for t in response.json())

    def test_filter_by_owner(self, client):
        _csv_upload(client, CHASE_CSV_CONTENT)
        response = client.get("/api/v1/transactions/?owner=alice")
        assert response.status_code == 200
        assert all(t["owner"] == "alice" for t in response.json())

    def test_pagination(self, client):
        _csv_upload(client, CHASE_CSV_CONTENT)
        response = client.get("/api/v1/transactions/?skip=1&limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1


class TestGetById:
    def test_get_found(self, client):
        upload = _csv_upload(client, CHASE_CSV_CONTENT)
        txn_id = upload.json()["transaction_ids"][0]
        response = client.get(f"/api/v1/transactions/{txn_id}")
        assert response.status_code == 200
        assert response.json()["id"] == txn_id

    def test_get_not_found(self, client):
        response = client.get("/api/v1/transactions/999999")
        assert response.status_code == 404


class TestDelete:
    def test_delete_success(self, client):
        upload = _csv_upload(client, CHASE_CSV_CONTENT)
        txn_id = upload.json()["transaction_ids"][0]
        response = client.delete(f"/api/v1/transactions/{txn_id}")
        assert response.status_code == 204
        assert client.get(f"/api/v1/transactions/{txn_id}").status_code == 404

    def test_delete_not_found(self, client):
        response = client.delete("/api/v1/transactions/999999")
        assert response.status_code == 404
