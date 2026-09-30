import io

from app.attachments import storage
from app.core.config import settings


def _create_service_entry(client):
    return client.post(
        "/api/service-entries",
        json={"date": "2026-08-02", "mileage_km": 10200, "type": "oil_change", "cost": 80},
    ).json()


def test_upload_and_download_attachment(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    entry = _create_service_entry(client)

    file_content = b"fake pdf content"
    response = client.post(
        f"/api/service-entries/{entry['id']}/attachments",
        files={"file": ("invoice.pdf", io.BytesIO(file_content), "application/pdf")},
    )
    assert response.status_code == 201
    attachment = response.json()
    assert attachment["filename"] == "invoice.pdf"

    entries = client.get("/api/service-entries").json()
    assert entries[0]["attachments"][0]["filename"] == "invoice.pdf"

    download = client.get(f"/api/attachments/{attachment['id']}/download")
    assert download.status_code == 200
    assert download.content == file_content


def test_upload_attachment_to_missing_entry_404s(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    response = client.post(
        "/api/service-entries/999/attachments",
        files={"file": ("x.pdf", io.BytesIO(b"x"), "application/pdf")},
    )
    assert response.status_code == 404


def test_delete_attachment_removes_file_and_record(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    entry = _create_service_entry(client)
    attachment = client.post(
        f"/api/service-entries/{entry['id']}/attachments",
        files={"file": ("invoice.pdf", io.BytesIO(b"data"), "application/pdf")},
    ).json()

    response = client.delete(f"/api/attachments/{attachment['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/attachments/{attachment['id']}/download").status_code == 404


def test_upload_rejects_disallowed_content_type(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    entry = _create_service_entry(client)

    response = client.post(
        f"/api/service-entries/{entry['id']}/attachments",
        files={"file": ("notes.txt", io.BytesIO(b"x"), "text/plain")},
    )
    assert response.status_code == 400
    assert "text/plain" in response.json()["detail"]
    assert client.get("/api/service-entries").json()[0]["attachments"] == []


def test_upload_rejects_oversized_file(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    monkeypatch.setattr(storage, "MAX_UPLOAD_BYTES", 1024)
    entry = _create_service_entry(client)

    response = client.post(
        f"/api/service-entries/{entry['id']}/attachments",
        files={"file": ("big.pdf", io.BytesIO(b"x" * 4096), "application/pdf")},
    )
    assert response.status_code == 400
    assert "velký" in response.json()["detail"]
    assert client.get("/api/service-entries").json()[0]["attachments"] == []
    assert list(tmp_path.glob("**/*.pdf")) == []


def test_listing_keeps_attachments_with_their_own_entry(client, monkeypatch, tmp_path):
    """The listing groups all attachments in one query, so a mix-up between
    entries would be the failure mode."""
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    first = _create_service_entry(client)
    second = client.post(
        "/api/service-entries",
        json={"date": "2026-08-20", "mileage_km": 10500, "type": "tires", "cost": 200},
    ).json()

    for entry, name in ((first, "first.pdf"), (second, "second.pdf")):
        response = client.post(
            f"/api/service-entries/{entry['id']}/attachments",
            files={"file": (name, io.BytesIO(b"data"), "application/pdf")},
        )
        assert response.status_code == 201

    by_id = {e["id"]: e for e in client.get("/api/service-entries").json()}
    assert [a["filename"] for a in by_id[first["id"]]["attachments"]] == ["first.pdf"]
    assert [a["filename"] for a in by_id[second["id"]]["attachments"]] == ["second.pdf"]


def test_deleting_entry_removes_its_attachments_and_they_never_reappear(
    client, monkeypatch, tmp_path
):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    entry = _create_service_entry(client)
    attachment = client.post(
        f"/api/service-entries/{entry['id']}/attachments",
        files={"file": ("invoice.pdf", io.BytesIO(b"data"), "application/pdf")},
    ).json()

    assert client.delete(f"/api/service-entries/{entry['id']}").status_code == 204
    assert client.get(f"/api/attachments/{attachment['id']}/download").status_code == 404
    assert list(tmp_path.iterdir()) == []

    new_entry = _create_service_entry(client)
    # SQLite hands out the freed id again; the deleted entry's invoice must not follow it.
    assert new_entry["id"] == entry["id"]
    assert client.get("/api/service-entries").json()[0]["attachments"] == []
