import pytest
from fastapi.testclient import TestClient

from app.main import VERSION, app


client = TestClient(app)


@pytest.mark.parametrize("method", ["get", "post"])
def test_png_response_has_png_magic_bytes(method: str) -> None:
    if method == "get":
        response = client.get("/qr", params={"data": "https://example.com"})
    else:
        response = client.post("/qr", json={"data": "https://example.com"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize("method", ["get", "post"])
def test_svg_response_has_svg_root(method: str) -> None:
    payload = {"data": "Hello, SVG", "format": "svg"}
    if method == "get":
        response = client.get("/qr", params=payload)
    else:
        response = client.post("/qr", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in response.content
    assert b"</svg>" in response.content


@pytest.mark.parametrize(
    ("params", "expected_location"),
    [
        ({}, "data"),
        ({"data": "x" * 2001}, "data"),
        ({"data": "hello", "scale": 0}, "scale"),
        ({"data": "hello", "scale": 21}, "scale"),
        ({"data": "hello", "border": -1}, "border"),
        ({"data": "hello", "border": 17}, "border"),
        ({"data": "hello", "dark": "nothex"}, "dark"),
        ({"data": "hello", "light": "fff"}, "light"),
        ({"data": "hello", "format": "pdf"}, "format"),
    ],
)
def test_get_validation_errors(params: dict[str, object], expected_location: str) -> None:
    response = client.get("/qr", params=params)

    assert response.status_code == 422
    assert any(error["loc"][-1] == expected_location for error in response.json()["detail"])


@pytest.mark.parametrize(
    ("payload", "expected_location"),
    [
        ({}, "data"),
        ({"data": "x" * 2001}, "data"),
        ({"data": "hello", "scale": 0}, "scale"),
        ({"data": "hello", "border": 17}, "border"),
        ({"data": "hello", "dark": "#000000"}, "dark"),
        ({"data": "hello", "light": "xyzxyz"}, "light"),
        ({"data": "hello", "format": "jpeg"}, "format"),
    ],
)
def test_post_validation_errors(payload: dict[str, object], expected_location: str) -> None:
    response = client.post("/qr", json=payload)

    assert response.status_code == 422
    assert any(error["loc"][-1] == expected_location for error in response.json()["detail"])


@pytest.mark.parametrize("method", ["get", "post"])
def test_valid_length_but_unencodable_data_returns_422(method: str) -> None:
    payload = {"data": "😀" * 2000}
    if method == "get":
        response = client.get("/qr", params=payload)
    else:
        response = client.post("/qr", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Data cannot be encoded as a QR code with the selected settings."
    )


def test_health_and_openapi() -> None:
    health = client.get("/health")
    openapi = client.get("/openapi.json")

    assert health.status_code == 200
    assert health.json() == {"status": "ok", "version": VERSION}
    assert openapi.status_code == 200
    assert "/qr" in openapi.json()["paths"]
    assert set(openapi.json()["paths"]["/qr"]) >= {"get", "post"}


def test_home_links_to_usage_and_docs() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'href="/qr?data=Hello%20world"' in response.text
    assert 'href="/docs"' in response.text


def test_cors_preflight_allows_post() -> None:
    response = client.options(
        "/qr",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "POST" in response.headers["access-control-allow-methods"]
