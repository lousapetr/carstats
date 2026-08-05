import io

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
