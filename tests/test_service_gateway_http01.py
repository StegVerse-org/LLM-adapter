from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from llm_adapter.deployed_gateway import app
from llm_adapter.service_gateway_http01 import HTTP01ProjectionError, read_http01_challenge


def test_deployed_gateway_serves_tvc_projected_public_http01(monkeypatch, tmp_path: Path) -> None:
    root=tmp_path/"http01"
    root.mkdir()
    (root/"token_ABC-123").write_text("token_ABC-123.thumbprint_public\n",encoding="ascii")
    monkeypatch.setenv("STEGVERSE_TVC_HTTP01_CHALLENGE_ROOT",str(root))
    response=TestClient(app).get("/.well-known/acme-challenge/token_ABC-123")
    assert response.status_code==200
    assert response.text=="token_ABC-123.thumbprint_public"
    assert response.headers["x-stegverse-credential-authority"]=="TV/TVC"
    assert response.headers["x-stegverse-authority-effect"]=="NONE"
    assert response.headers["cache-control"]=="no-store"


def test_missing_challenge_is_404(monkeypatch, tmp_path: Path) -> None:
    root=tmp_path/"http01"
    root.mkdir()
    monkeypatch.setenv("STEGVERSE_TVC_HTTP01_CHALLENGE_ROOT",str(root))
    response=TestClient(app).get("/.well-known/acme-challenge/missing")
    assert response.status_code==404


@pytest.mark.parametrize("token",["../escape","a/b","", "token space", "."*129])
def test_invalid_tokens_fail_closed(token: str,tmp_path: Path) -> None:
    with pytest.raises(HTTP01ProjectionError):
        read_http01_challenge(token,root=tmp_path)


def test_symlink_and_oversize_challenges_fail_closed(tmp_path: Path) -> None:
    outside=tmp_path/"outside"
    outside.write_text("public",encoding="ascii")
    root=tmp_path/"root"
    root.mkdir()
    link=root/"link"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(HTTP01ProjectionError,match="symlink"):
        read_http01_challenge("link",root=root)
    (root/"big").write_text("x"*513,encoding="ascii")
    with pytest.raises(HTTP01ProjectionError,match="size"):
        read_http01_challenge("big",root=root)


def test_route_registration_is_public_read_only() -> None:
    routes=[r for r in app.routes if getattr(r,"path","") == "/.well-known/acme-challenge/{token}"]
    assert len(routes)==1
    assert routes[0].methods=={"GET"}
