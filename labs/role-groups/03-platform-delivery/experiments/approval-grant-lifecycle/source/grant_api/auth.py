from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    roles: frozenset[str]
    scopes: frozenset[str]


def _roles(claims: dict[str, Any], audience: str) -> frozenset[str]:
    result: set[str] = set((claims.get("realm_access") or {}).get("roles") or [])
    result.update(((claims.get("resource_access") or {}).get(audience) or {}).get("roles") or [])
    result.update(claims.get("roles") or [])
    result.update(str(group).strip("/") for group in (claims.get("groups") or []))
    return frozenset(str(role) for role in result)


def current_principal(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_dev_user: Annotated[str | None, Header()] = None,
    x_dev_roles: Annotated[str | None, Header()] = None,
    x_dev_scopes: Annotated[str | None, Header()] = None,
) -> Principal:
    settings = request.app.state.settings
    if settings.auth_mode == "dev":
        if not x_dev_user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "X-Dev-User is required in dev mode")
        return Principal(
            x_dev_user,
            frozenset(item.strip() for item in (x_dev_roles or "").split(",") if item.strip()),
            frozenset((x_dev_scopes or "").split()),
        )
    if settings.auth_mode != "oidc":
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "unsupported AUTH_MODE")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token is required")
    bearer_assertion = authorization.split(" ", 1)[1]
    if not settings.oidc_issuer or not settings.oidc_jwks_url or not settings.oidc_audience:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "OIDC is not configured")
    try:
        key = PyJWKClient(settings.oidc_jwks_url).get_signing_key_from_jwt(bearer_assertion).key
        claims = jwt.decode(
            bearer_assertion,
            key,
            algorithms=["RS256", "ES256"],
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except (jwt.PyJWTError, PyJWKClientError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid access token") from exc
    return Principal(
        str(claims["sub"]),
        _roles(claims, settings.oidc_audience),
        frozenset(str(claims.get("scope", "")).split()),
    )


def require_roles(*allowed_roles: str, scopes: tuple[str, ...] = ()):
    allowed = frozenset(allowed_roles)
    required_scopes = frozenset(scopes)

    def dependency(
        request: Request,
        principal: Annotated[Principal, Depends(current_principal)],
    ) -> Principal:
        if not principal.roles.intersection(allowed):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "required role is missing")
        if request.app.state.settings.auth_mode == "oidc" and not required_scopes.issubset(
            principal.scopes
        ):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "required scope is missing")
        return principal

    return dependency
