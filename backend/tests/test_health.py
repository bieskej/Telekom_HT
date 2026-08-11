def test_health_pdf_font_dejavu(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["pdf_font"] == "dejavu"
    assert data["cwd_matches_backend"] is True
    assert "DejaVuSans" in str(data.get("fonts_dir", "")) or "fonts" in str(data.get("fonts_dir", ""))
