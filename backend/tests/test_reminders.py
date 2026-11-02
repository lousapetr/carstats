from datetime import date, timedelta

import pytest


def test_reminder_status_ok_when_far_from_due(client):
    reminder = client.post(
        "/api/reminders", json={"title": "Oil change", "due_mileage_km": 50000}
    ).json()
    assert reminder["status"] == "ok"


def test_reminder_status_due_soon_within_threshold(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    reminder = client.post(
        "/api/reminders", json={"title": "Oil change", "due_mileage_km": 10400}
    ).json()
    assert reminder["status"] == "due_soon"


def test_reminder_status_overdue_by_mileage(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    reminder = client.post(
        "/api/reminders", json={"title": "Oil change", "due_mileage_km": 9000}
    ).json()
    assert reminder["status"] == "overdue"


def test_reminder_status_overdue_by_date(client):
    reminder = client.post(
        "/api/reminders", json={"title": "Highway ticket", "due_date": "2020-01-01"}
    ).json()
    assert reminder["status"] == "overdue"


def test_completing_non_recurring_reminder_hides_it(client):
    reminder = client.post("/api/reminders", json={"title": "One-off task"}).json()
    complete = client.post(f"/api/reminders/{reminder['id']}/complete").json()
    assert complete["completed_at"] is not None
    assert client.get("/api/reminders").json() == []


def test_completing_recurring_reminder_rolls_forward(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    reminder = client.post(
        "/api/reminders",
        json={"title": "Oil change", "due_mileage_km": 10600, "recurrence_km": 10000},
    ).json()
    completed = client.post(f"/api/reminders/{reminder['id']}/complete").json()
    assert completed["completed_at"] is None
    assert completed["due_mileage_km"] == 20600
    assert completed["status"] == "ok"


def test_update_reminder(client):
    reminder = client.post(
        "/api/reminders", json={"title": "Oil change", "due_mileage_km": 50000}
    ).json()

    updated = client.put(
        f"/api/reminders/{reminder['id']}",
        json={"title": "Oil change (renamed)", "due_mileage_km": 60000},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["title"] == "Oil change (renamed)"
    assert body["due_mileage_km"] == 60000


def test_update_missing_reminder_404s(client):
    response = client.put(
        "/api/reminders/999", json={"title": "Oil change", "due_mileage_km": 50000}
    )
    assert response.status_code == 404


def test_delete_reminder(client):
    reminder = client.post("/api/reminders", json={"title": "Test"}).json()
    response = client.delete(f"/api/reminders/{reminder['id']}")
    assert response.status_code == 204
    assert client.get("/api/reminders").json() == []


def test_completing_reminder_recurring_by_days_without_due_date(client):
    reminder = client.post(
        "/api/reminders", json={"title": "Olej", "recurrence_days": 180}
    ).json()
    assert reminder["due_date"] is None

    completed = client.post(f"/api/reminders/{reminder['id']}/complete").json()
    assert completed["completed_at"] is None
    assert completed["due_date"] == str(date.today() + timedelta(days=180))
    assert completed["status"] == "ok"


def test_completing_reminder_recurring_by_km_without_due_mileage(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    reminder = client.post(
        "/api/reminders", json={"title": "Olej", "recurrence_km": 15000}
    ).json()
    assert reminder["due_mileage_km"] is None

    completed = client.post(f"/api/reminders/{reminder['id']}/complete").json()
    assert completed["completed_at"] is None
    assert completed["due_mileage_km"] == 25000
    assert completed["status"] == "ok"


@pytest.mark.parametrize(
    "override",
    [
        {"title": ""},
        {"title": "x" * 201},
        {"notes": "x" * 1001},
        {"due_mileage_km": -1},
        {"recurrence_days": 0},
        {"recurrence_days": -30},
        {"recurrence_km": 0},
        {"recurrence_km": -1000},
    ],
)
def test_create_reminder_rejects_out_of_range_values(client, override):
    response = client.post("/api/reminders", json={"title": "Oil change"} | override)
    assert response.status_code == 422
    assert client.get("/api/reminders").json() == []


def test_update_reminder_rejects_negative_recurrence(client):
    reminder = client.post("/api/reminders", json={"title": "Oil change"}).json()
    response = client.put(
        f"/api/reminders/{reminder['id']}",
        json={"title": "Oil change", "recurrence_days": -30},
    )
    assert response.status_code == 422


def test_completing_recurring_reminder_always_moves_due_date_forward(client):
    reminder = client.post(
        "/api/reminders",
        json={"title": "Highway ticket", "due_date": "2020-01-01", "recurrence_days": 365},
    ).json()
    assert reminder["status"] == "overdue"

    previous_due = date.fromisoformat(reminder["due_date"])
    for _ in range(3):
        completed = client.post(f"/api/reminders/{reminder['id']}/complete").json()
        due = date.fromisoformat(completed["due_date"])
        assert due > previous_due
        assert due > date.today()
        assert completed["status"] != "overdue"
        previous_due = due


def test_duplicate_active_reminder_is_rejected(client):
    body = {"title": "Oil change", "due_date": "2027-01-01", "due_mileage_km": 20000}
    client.post("/api/reminders", json=body)
    response = client.post("/api/reminders", json={**body, "title": " oil CHANGE "})
    assert response.status_code == 409
    assert "se stejným termínem" in response.json()["detail"]


def test_duplicate_reminder_without_due_fields_is_rejected(client):
    client.post("/api/reminders", json={"title": "Wash"})
    assert client.post("/api/reminders", json={"title": "wash"}).status_code == 409


def test_reminder_with_different_due_date_is_not_duplicate(client):
    client.post("/api/reminders", json={"title": "Oil change", "due_date": "2027-01-01"})
    response = client.post("/api/reminders", json={"title": "Oil change", "due_date": "2028-01-01"})
    assert response.status_code == 201


def test_completed_reminder_does_not_block_a_new_one(client):
    body = {"title": "Highway ticket", "due_date": "2027-01-01"}
    first = client.post("/api/reminders", json=body).json()
    client.post(f"/api/reminders/{first['id']}/complete")
    assert client.post("/api/reminders", json=body).status_code == 201


def test_duplicate_reminder_saved_with_force(client):
    client.post("/api/reminders", json={"title": "Wash"})
    assert client.post("/api/reminders?force=true", json={"title": "Wash"}).status_code == 201


def test_update_reminder_ignores_itself(client):
    reminder = client.post("/api/reminders", json={"title": "Wash"}).json()
    response = client.put(f"/api/reminders/{reminder['id']}", json={"title": "Wash", "notes": "x"})
    assert response.status_code == 200
