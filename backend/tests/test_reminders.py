def test_reminder_status_ok_when_far_from_due(client):
    reminder = client.post(
        "/api/reminders", json={"title": "Oil change", "due_mileage_km": 50000}
    ).json()
    assert reminder["status"] == "ok"


def test_reminder_status_due_soon_within_threshold(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_total": 60},
    )
    reminder = client.post(
        "/api/reminders", json={"title": "Oil change", "due_mileage_km": 10400}
    ).json()
    assert reminder["status"] == "due_soon"


def test_reminder_status_overdue_by_mileage(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_total": 60},
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
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_total": 60},
    )
    reminder = client.post(
        "/api/reminders",
        json={"title": "Oil change", "due_mileage_km": 10600, "recurrence_km": 10000},
    ).json()
    completed = client.post(f"/api/reminders/{reminder['id']}/complete").json()
    assert completed["completed_at"] is None
    assert completed["due_mileage_km"] == 20600
    assert completed["status"] == "ok"


def test_delete_reminder(client):
    reminder = client.post("/api/reminders", json={"title": "Test"}).json()
    response = client.delete(f"/api/reminders/{reminder['id']}")
    assert response.status_code == 204
    assert client.get("/api/reminders").json() == []
