# QR Code API

**Live instance:** https://qr.lifestep.io — try `/health`, and see `/openapi.json` for the full spec. Free, no signup.

**Self-host it:** `docker compose up -d` (see below). MIT licensed.

A small, stateless FastAPI service that generates QR codes from text or URLs. It returns either PNG bytes or an SVG document and is suitable for placing behind an API gateway such as RapidAPI.

## Run locally

Requires Python 3.12 or newer.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8085
```

Open <http://127.0.0.1:8085/docs> for interactive OpenAPI documentation.

## API

Both QR endpoints accept these values:

| Field | Required | Default | Rules |
| --- | --- | --- | --- |
| `data` | yes | — | 1–2000 characters |
| `format` | no | `png` | `png` or `svg` |
| `scale` | no | `6` | integer from 1 to 20 |
| `border` | no | `4` | integer from 0 to 16 |
| `dark` | no | `000000` | six-character RGB hex, without `#` |
| `light` | no | `ffffff` | six-character RGB hex, without `#` |

### GET `/qr`

```bash
curl --get 'http://127.0.0.1:8085/qr' \
  --data-urlencode 'data=https://example.com' \
  --data 'format=png' \
  --data 'scale=6' \
  --output qr.png
```

SVG with custom colors:

```bash
curl --get 'http://127.0.0.1:8085/qr' \
  --data-urlencode 'data=Hello world' \
  --data 'format=svg' \
  --data 'dark=172554' \
  --data 'light=eff6ff' \
  --output qr.svg
```

### POST `/qr`

```bash
curl 'http://127.0.0.1:8085/qr' \
  --header 'Content-Type: application/json' \
  --data '{"data":"https://example.com","format":"png","scale":8,"border":4}' \
  --output qr.png
```

### Other endpoints

- `GET /health` returns service status and version.
- `GET /` returns a minimal usage page.
- `GET /openapi.json` returns the OpenAPI schema.

## Docker

```bash
docker compose up --build
```

The Compose service is available at <http://127.0.0.1:8085>. Stop it with `docker compose down`.

## Tests

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
PYTHONPATH=. .venv/bin/pytest -q
```

## Honest limits

- The API holds generated images in memory and is intended for small, individual requests.
- The 2000-character input limit is an API ceiling, not a guarantee that every value can fit in a QR symbol. Encodability also depends on character encoding; unencodable inputs return HTTP `422`.
- There is no authentication, per-customer quota, rate limiting, billing, caching, persistence, or abuse protection in this service.
- Very low color contrast can produce a QR code that scanners cannot read. The API validates color syntax, not contrast or scan reliability.
- SVG output is generated from the submitted data and should be served with the declared `image/svg+xml` content type.

## RapidAPI-ready note

The stateless HTTP interface, CORS support, stable query/body schema, health endpoint, and OpenAPI document make the service straightforward to put behind RapidAPI or another gateway. Before publishing, configure gateway authentication, quotas, rate limits, request-size and timeout limits, monitoring, HTTPS, and commercial terms. None of those gateway controls are simulated by this repository.
