import io

from app.core.config import settings

FUEL = "/api/fuel-entries"
SERVICE = "/api/service-entries"


def _fuel(client, date, mileage_km, liters=40, **extra):
    return client.post(
        FUEL,
        json={
            "date": date,
            "mileage_km": mileage_km,
            "liters": liters,
            "price_per_liter": 1.5,
            **extra,
        },
    )


def _service(client, date, mileage_km, **extra):
    return client.post(
        SERVICE,
        json={
            "date": date,
            "mileage_km": mileage_km,
            "type": "oil_change",
            "cost": 80,
            **extra,
        },
    )


def test_fuel_draft_with_only_mileage(client):
    response = client.post(FUEL, json={"is_draft": True, "mileage_km": 12000})
    assert response.status_code == 201
    body = response.json()
    assert body["is_draft"] is True
    assert body["date"] is None
    assert body["liters"] is None
    assert body["price_per_liter"] is None
    assert body["price_total"] is None
    assert body["price_total_czk"] is None
    assert body["price_per_liter_czk"] is None


def test_fuel_draft_with_only_notes(client):
    response = client.post(FUEL, json={"is_draft": True, "notes": "doplnit"})
    assert response.status_code == 201
    assert response.json()["mileage_km"] is None


def test_service_draft_with_only_mileage(client):
    response = client.post(SERVICE, json={"is_draft": True, "mileage_km": 12000, "type": "tires"})
    assert response.status_code == 201
    body = response.json()
    assert body["is_draft"] is True
    assert body["date"] is None
    assert body["cost"] is None
    assert body["cost_czk"] is None


def test_service_draft_with_only_notes(client):
    response = client.post(
        SERVICE, json={"is_draft": True, "type": "other", "notes": "zjistit cenu"}
    )
    assert response.status_code == 201


def test_draft_without_substantive_field_is_rejected(client):
    fuel = client.post(
        FUEL, json={"is_draft": True, "date": "2026-08-01", "currency": "EUR", "notes": "  "}
    )
    assert fuel.status_code == 422
    assert "aspoň jeden údaj" in fuel.json()["detail"][0]["msg"]
    service = client.post(
        SERVICE, json={"is_draft": True, "date": "2026-08-01", "type": "tires", "description": ""}
    )
    assert service.status_code == 422


def test_complete_entry_missing_required_field_is_rejected(client):
    fuel = client.post(FUEL, json={"date": "2026-08-01", "mileage_km": 1000, "liters": 40})
    assert fuel.status_code == 422
    assert "cena za litr" in fuel.json()["detail"][0]["msg"]
    service = client.post(SERVICE, json={"date": "2026-08-01", "type": "tires", "cost": 5})
    assert service.status_code == 422
    assert "stav tachometru" in service.json()["detail"][0]["msg"]


def test_draft_skips_mileage_consistency_and_does_not_move_current_mileage(client):
    _fuel(client, "2026-08-01", 10000)
    _service(client, "2026-08-02", 10100)
    assert (
        client.post(
            FUEL, json={"is_draft": True, "date": "2026-07-01", "mileage_km": 99999}
        ).status_code
        == 201
    )
    assert (
        client.post(
            SERVICE,
            json={"is_draft": True, "date": "2026-07-01", "mileage_km": 99999, "type": "tires"},
        ).status_code
        == 201
    )
    assert client.get("/api/car").json()["current_mileage_km"] == 10100


def test_draft_skips_duplicate_check_and_does_not_block_complete_entries(client):
    first = client.post(FUEL, json={"is_draft": True, "date": "2026-08-01", "mileage_km": 10000})
    again = client.post(FUEL, json={"is_draft": True, "date": "2026-08-01", "mileage_km": 10000})
    assert first.status_code == again.status_code == 201
    assert _fuel(client, "2026-08-01", 10000).status_code == 201

    s_draft = client.post(
        SERVICE,
        json={"is_draft": True, "date": "2026-08-02", "mileage_km": 10100, "type": "oil_change"},
    )
    assert s_draft.status_code == 201
    assert _service(client, "2026-08-02", 10100).status_code == 201


def test_finishing_a_draft_validates_mileage_then_updates_current_mileage(client):
    _fuel(client, "2026-08-01", 10000)
    _fuel(client, "2026-09-01", 11000)
    draft = client.post(FUEL, json={"is_draft": True, "mileage_km": 50000}).json()
    complete = {
        "date": "2026-08-15",
        "mileage_km": 50000,
        "liters": 30,
        "price_per_liter": 1.4,
        "is_draft": False,
    }
    bad = client.put(f"{FUEL}/{draft['id']}", json=complete)
    assert bad.status_code == 400
    assert client.get("/api/car").json()["current_mileage_km"] == 11000

    ok = client.put(f"{FUEL}/{draft['id']}", json={**complete, "mileage_km": 10500})
    assert ok.status_code == 200
    assert ok.json()["is_draft"] is False
    assert client.get("/api/car").json()["current_mileage_km"] == 11000

    top = client.post(FUEL, json={"is_draft": True, "mileage_km": 20000}).json()
    done = client.put(
        f"{FUEL}/{top['id']}", json={**complete, "date": "2026-10-01", "mileage_km": 20000}
    )
    assert done.status_code == 200
    assert client.get("/api/car").json()["current_mileage_km"] == 20000


def test_finishing_a_draft_runs_the_duplicate_check(client):
    _fuel(client, "2026-08-01", 10000)
    draft = client.post(FUEL, json={"is_draft": True, "mileage_km": 10000}).json()
    body = {
        "date": "2026-08-01",
        "mileage_km": 10000,
        "liters": 30,
        "price_per_liter": 1.4,
    }
    assert client.put(f"{FUEL}/{draft['id']}", json=body).status_code == 409
    assert client.put(f"{FUEL}/{draft['id']}?force=true", json=body).status_code == 200


def test_finishing_a_service_draft(client):
    _service(client, "2026-08-01", 10000)
    _service(client, "2026-09-01", 11000)
    draft = client.post(
        SERVICE, json={"is_draft": True, "type": "tires", "description": "zimní"}
    ).json()
    complete = {
        "date": "2026-08-15",
        "mileage_km": 50000,
        "type": "tires",
        "description": "zimní",
        "cost": 4000,
        "is_draft": False,
    }
    incomplete = client.put(f"{SERVICE}/{draft['id']}", json={**complete, "cost": None})
    assert incomplete.status_code == 422
    assert client.put(f"{SERVICE}/{draft['id']}", json=complete).status_code == 400

    ok = client.put(f"{SERVICE}/{draft['id']}", json={**complete, "mileage_km": 10500})
    assert ok.status_code == 200
    assert ok.json()["is_draft"] is False
    assert ok.json()["cost_czk"] == 4000

    dup = client.post(
        SERVICE, json={"is_draft": True, "type": "oil_change", "mileage_km": 10000}
    ).json()
    finish_dup = {"date": "2026-08-01", "mileage_km": 10000, "type": "oil_change", "cost": 80}
    assert client.put(f"{SERVICE}/{dup['id']}", json=finish_dup).status_code == 409


def test_finishing_a_draft_takes_the_current_exchange_rate(client, monkeypatch):
    fuel = client.post(FUEL, json={"is_draft": True, "liters": 30, "currency": "EUR"}).json()
    service = client.post(
        SERVICE, json={"is_draft": True, "type": "tires", "cost": 100, "currency": "EUR"}
    ).json()
    assert fuel["exchange_rate"] == service["exchange_rate"] == 25.0

    monkeypatch.setattr("app.fuel.service.get_rate", lambda db, currency: 26.0)
    monkeypatch.setattr("app.maintenance.service.get_rate", lambda db, currency: 26.0)
    done_fuel = client.put(
        f"{FUEL}/{fuel['id']}",
        json={
            "date": "2026-08-01",
            "mileage_km": 10000,
            "liters": 30,
            "price_per_liter": 2,
            "currency": "EUR",
        },
    ).json()
    assert done_fuel["exchange_rate"] == 26.0
    assert done_fuel["price_total_czk"] == 1560
    done_service = client.put(
        f"{SERVICE}/{service['id']}",
        json={
            "date": "2026-08-02",
            "mileage_km": 10100,
            "type": "tires",
            "cost": 100,
            "currency": "EUR",
        },
    ).json()
    assert done_service["exchange_rate"] == 26.0
    assert done_service["cost_czk"] == 2600


def test_deleting_drafts(client):
    _fuel(client, "2026-08-01", 10000)
    fuel = client.post(FUEL, json={"is_draft": True, "mileage_km": 99999}).json()
    service = client.post(SERVICE, json={"is_draft": True, "type": "tires", "cost": 5}).json()
    assert client.delete(f"{FUEL}/{fuel['id']}").status_code == 204
    assert client.delete(f"{SERVICE}/{service['id']}").status_code == 204
    assert [e["is_draft"] for e in client.get(FUEL).json()] == [False]
    assert client.get(SERVICE).json() == []
    assert client.get("/api/dashboard").json()["drafts"] == []
    assert client.get("/api/car").json()["current_mileage_km"] == 10000


def test_draft_accepts_attachments_and_keeps_them_when_finished(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    draft = client.post(
        SERVICE, json={"is_draft": True, "type": "other", "notes": "faktura"}
    ).json()
    upload = client.post(
        f"{SERVICE}/{draft['id']}/attachments",
        files={"file": ("invoice.pdf", io.BytesIO(b"pdf"), "application/pdf")},
    )
    assert upload.status_code == 201
    listed = client.get(SERVICE).json()[0]
    assert listed["is_draft"] is True
    assert [a["filename"] for a in listed["attachments"]] == ["invoice.pdf"]

    done = client.put(
        f"{SERVICE}/{draft['id']}",
        json={"date": "2026-08-01", "mileage_km": 10000, "type": "other", "cost": 50},
    )
    assert done.status_code == 200
    assert [a["filename"] for a in done.json()["attachments"]] == ["invoice.pdf"]

    assert client.delete(f"{SERVICE}/{draft['id']}").status_code == 204
    assert not (tmp_path / str(draft["id"])).exists()


def test_validation_messages_have_no_english_prefix(client):
    empty = client.post(FUEL, json={"is_draft": True}).json()["detail"][0]["msg"]
    assert empty == "Rozpracovaný záznam musí obsahovat aspoň jeden údaj."
    missing = client.post(SERVICE, json={"type": "tires"}).json()["detail"][0]["msg"]
    assert missing == "Chybí povinné údaje: datum, stav tachometru, cena."


def test_complete_entry_can_become_a_draft(client):
    created = _fuel(client, "2026-08-01", 10000).json()
    response = client.put(f"{FUEL}/{created['id']}", json={"is_draft": True, "mileage_km": 10000})
    assert response.status_code == 200
    assert response.json()["is_draft"] is True
    assert client.get("/api/car").json()["current_mileage_km"] == 0


def test_lists_put_drafts_first_newest_created_first(client):
    _fuel(client, "2026-08-01", 10000)
    first = client.post(FUEL, json={"is_draft": True, "notes": "a"}).json()
    second = client.post(FUEL, json={"is_draft": True, "notes": "b"}).json()
    _fuel(client, "2026-08-05", 10500)
    entries = client.get(FUEL).json()
    assert [e["id"] for e in entries[:2]] == [second["id"], first["id"]]
    assert [e["mileage_km"] for e in entries[2:]] == [10500, 10000]

    _service(client, "2026-08-02", 10200)
    s1 = client.post(SERVICE, json={"is_draft": True, "type": "tires", "notes": "a"}).json()
    s2 = client.post(SERVICE, json={"is_draft": True, "type": "tires", "notes": "b"}).json()
    _service(client, "2026-08-09", 10900)
    services = client.get(SERVICE).json()
    assert [e["id"] for e in services[:2]] == [s2["id"], s1["id"]]
    assert [e["mileage_km"] for e in services[2:]] == [10900, 10200]


def test_consumption_ignores_drafts(client):
    _fuel(client, "2026-08-01", 10000)
    draft = client.post(
        FUEL, json={"is_draft": True, "mileage_km": 10250, "liters": 99, "full_tank": True}
    ).json()
    assert draft["consumption_l_per_100km"] is None
    closing = _fuel(client, "2026-08-05", 10500, liters=35).json()
    assert closing["consumption_l_per_100km"] == 7.0
    entries = client.get(FUEL).json()
    by_id = {e["id"]: e for e in entries}
    assert by_id[draft["id"]]["consumption_l_per_100km"] is None
    assert by_id[closing["id"]]["consumption_l_per_100km"] == 7.0


def test_dashboard_excludes_drafts_and_lists_them(client):
    _fuel(client, "2026-08-01", 10000)
    _fuel(client, "2026-08-05", 10500, liters=35)
    _service(client, "2026-08-06", 10600)
    fuel_draft = client.post(
        FUEL,
        json={
            "is_draft": True,
            "date": "2026-08-07",
            "mileage_km": 10700,
            "liters": 20,
            "price_per_liter": 2,
            "currency": "EUR",
        },
    ).json()
    service_draft = client.post(
        SERVICE, json={"is_draft": True, "type": "tires", "description": "zimní", "cost": 5000}
    ).json()

    body = client.get("/api/dashboard?period=all").json()
    assert body["totals"]["fuel_entries"] == 2
    assert body["totals"]["maintenance_entries"] == 1
    assert body["totals"]["fuel_liters"] == 75
    assert len(body["activity"]) == 3
    assert len(body["fuel_trend"]) == 2
    assert body["available_years"] == [2026]
    assert body["car"]["current_mileage_km"] == 10600
    assert body["totals"]["fuel"] == 112.5
    assert body["totals"]["maintenance"] == 80
    assert body["totals"]["total"] == 192.5
    assert body["distance_km"] == 600
    assert body["avg_consumption_l_per_100km"] == 7.0
    assert body["consumption_interval_count"] == 1
    assert body["avg_price_per_liter"] == 1.5
    assert body["cost_breakdown"]["fuel_total"] == 112.5
    assert body["cost_breakdown"]["maintenance_by_type"] == {"oil_change": 80}
    assert sum(m["fuel"] for m in body["monthly_costs"]) == 112.5
    assert sum(m["service"] for m in body["monthly_costs"]) == 80

    assert [(d["kind"], d["id"]) for d in body["drafts"]] == [
        ("service", service_draft["id"]),
        ("fuel", fuel_draft["id"]),
    ]
    fuel_item = body["drafts"][1]
    assert fuel_item["price_total"] == 40.0
    assert fuel_item["currency"] == "EUR"
    assert body["drafts"][0]["description"] == "zimní"
    assert body["drafts"][0]["date"] is None


def test_dashboard_previous_period_excludes_drafts(client):
    _fuel(client, "2025-03-01", 9000)
    _fuel(client, "2026-03-01", 10000)
    client.post(
        FUEL,
        json={"is_draft": True, "date": "2025-04-01", "liters": 50, "price_per_liter": 2},
    )
    client.post(
        SERVICE, json={"is_draft": True, "date": "2025-04-02", "type": "tires", "cost": 900}
    )
    body = client.get("/api/dashboard?period=year:2026").json()
    assert body["previous_totals"]["fuel"] == 60
    assert body["previous_totals"]["fuel_entries"] == 1
    assert body["previous_totals"]["maintenance"] == 0
    assert body["total_cost_delta_pct"] == 0


def test_dashboard_drafts_ignore_the_period(client):
    client.post(FUEL, json={"is_draft": True, "mileage_km": 1})
    assert len(client.get("/api/dashboard?period=year:1999").json()["drafts"]) == 1


def test_export_excludes_drafts(client):
    _fuel(client, "2026-08-01", 10000)
    _service(client, "2026-08-02", 10200)
    client.post(FUEL, json={"is_draft": True, "mileage_km": 77777})
    client.post(SERVICE, json={"is_draft": True, "type": "tires", "mileage_km": 88888})
    assert "77777" not in client.get("/api/export/fuel.csv").text
    assert "88888" not in client.get("/api/export/maintenance.csv").text
    assert "10000" in client.get("/api/export/fuel.csv").text
