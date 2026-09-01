from __future__ import annotations

from io import BytesIO
from typing import Annotated, Literal

import segno
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, ConfigDict, Field

VERSION = "1.0.0"
HEX_COLOR_PATTERN = r"^[0-9a-fA-F]{6}$"


class QRRequest(BaseModel):
    """Validated JSON payload for QR generation."""

    model_config = ConfigDict(extra="forbid")

    data: str = Field(min_length=1, max_length=2000)
    format: Literal["png", "svg"] = "png"
    scale: int = Field(default=6, ge=1, le=20)
    border: int = Field(default=4, ge=0, le=16)
    dark: str = Field(default="000000", pattern=HEX_COLOR_PATTERN)
    light: str = Field(default="ffffff", pattern=HEX_COLOR_PATTERN)


app = FastAPI(
    title="QR Code API",
    description="Generate PNG or SVG QR codes from text and URLs.",
    version=VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def render_qr(request: QRRequest) -> Response:
    """Render a validated request as an in-memory PNG or SVG response."""

    try:
        # Always emit a standard QR Code. Segno may otherwise choose a Micro QR
        # symbol for short values, which has less scanner support.
        qr = segno.make_qr(request.data, error="m")
    except (segno.DataOverflowError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Data cannot be encoded as a QR code with the selected settings.",
        ) from exc

    output = BytesIO()
    qr.save(
        output,
        kind=request.format,
        scale=request.scale,
        border=request.border,
        dark=f"#{request.dark}",
        light=f"#{request.light}",
    )

    media_type = "image/png" if request.format == "png" else "image/svg+xml"
    return Response(
        content=output.getvalue(),
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="qr-code.{request.format}"'},
    )


@app.get("/qr", response_class=Response, tags=["QR codes"])
def get_qr(
    data: Annotated[str, Query(min_length=1, max_length=2000)],
    format: Annotated[Literal["png", "svg"], Query()] = "png",
    scale: Annotated[int, Query(ge=1, le=20)] = 6,
    border: Annotated[int, Query(ge=0, le=16)] = 4,
    dark: Annotated[str, Query(pattern=HEX_COLOR_PATTERN)] = "000000",
    light: Annotated[str, Query(pattern=HEX_COLOR_PATTERN)] = "ffffff",
) -> Response:
    """Generate a QR code using query-string parameters."""

    return render_qr(
        QRRequest(
            data=data,
            format=format,
            scale=scale,
            border=border,
            dark=dark,
            light=light,
        )
    )


@app.post("/qr", response_class=Response, tags=["QR codes"])
def post_qr(request: QRRequest) -> Response:
    """Generate a QR code using a JSON request body."""

    return render_qr(request)


@app.get("/health", tags=["Service"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": VERSION}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> HTMLResponse:
    return HTMLResponse(
        """<!doctype html>
<html lang="en">
  <head><meta charset="utf-8"><title>QR Code API</title></head>
  <body>
    <h1>QR Code API</h1>
    <p>Generate PNG or SVG QR codes from text and URLs.</p>
    <p><a href="/qr?data=Hello%20world">Try a PNG</a> · <a href="/docs">API docs</a></p>
  </body>
</html>"""
    )
