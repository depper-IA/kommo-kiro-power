"""
Kommo API v4 Client
==================
Handles all HTTP communication with Kommo, including:
- OAuth token refresh
- Rate limiting (5 req/sec)
- Retry with exponential backoff
- Response caching
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

import httpx
from dotenv import set_key

logger = logging.getLogger("kommo_client")

# --- Constants ---
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
RATE_LIMIT = 5  # requests per second
TIMEOUT = 30  # seconds

ENV_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
)


# --- Cache ---
_cache: dict[str, dict[str, Any]] = {}


def cache_get(key: str) -> Any | None:
    """Get cached value if not expired."""
    entry = _cache.get(key)
    if entry and time.time() < entry["expires"]:
        return entry["data"]
    _cache.pop(key, None)
    return None


def cache_set(key: str, data: Any, ttl: int) -> None:
    """Set cached value with TTL in seconds."""
    _cache[key] = {"data": data, "expires": time.time() + ttl}


def cache_invalidate(*keys: str) -> None:
    """Invalidate cached entries."""
    for key in keys:
        _cache.pop(key, None)


class KommoClient:
    """
    HTTP client for Kommo CRM API v4.

    Features:
    - Automatic token refresh on 401
    - Rate limiting (5 req/sec)
    - Exponential backoff on failures
    - Response caching for pipelines/stages/fields
    """

    def __init__(self) -> None:
        from dotenv import load_dotenv

        load_dotenv(os.path.normpath(ENV_PATH), override=True)

        self.subdomain = os.getenv("KOMMO_SUBDOMAIN", "")
        self.client_id = os.getenv("KOMMO_CLIENT_ID", "")
        self.client_secret = os.getenv("KOMMO_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("KOMMO_REDIRECT_URI", "http://localhost:8080/callback")
        self.access_token = os.getenv("KOMMO_ACCESS_TOKEN", "")
        self.refresh_token = os.getenv("KOMMO_REFRESH_TOKEN", "")
        self.base_url = f"https://{self.subdomain}.kommo.com/api/v4"

        self._client = httpx.AsyncClient(timeout=TIMEOUT)
        self._tags_cache: dict[str, int] = {}
        self._request_times: list[float] = []

    # --- Internal HTTP ---

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def _rate_limit_wait(self) -> None:
        """Throttle to max 5 requests per second."""
        now = time.time()
        self._request_times = [t for t in self._request_times if now - t < 1.0]
        if len(self._request_times) >= RATE_LIMIT:
            sleep_time = 1.0 - (now - self._request_times[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
        self._request_times.append(time.time())

    async def _sleep_with_backoff(self, attempt: int) -> None:
        """Exponential backoff: 1s, 2s, 4s..."""
        delay = BASE_DELAY * (2**attempt)
        jitter = delay * 0.1 * (time.time() % 1)
        logger.warning(f"Retry in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
        await asyncio.sleep(delay + jitter)

    async def _refresh_tokens(self) -> None:
        """Refresh access token using refresh_token."""
        logger.info("Refreshing access token...")
        resp = await self._client.post(
            f"https://{self.subdomain}.kommo.com/oauth2/access_token",
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "redirect_uri": self.redirect_uri,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        set_key(ENV_PATH, "KOMMO_ACCESS_TOKEN", self.access_token)
        set_key(ENV_PATH, "KOMMO_REFRESH_TOKEN", self.refresh_token)
        logger.info("Tokens refreshed successfully")

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make HTTP request with retry logic and rate limiting."""
        await self._rate_limit_wait()
        url = f"{self.base_url}{endpoint}" if endpoint.startswith("/") else endpoint

        for attempt in range(MAX_RETRIES):
            try:
                resp = await self._client.request(method, url, headers=self._headers(), **kwargs)

                if resp.status_code == 401:
                    await self._refresh_tokens()
                    resp = await self._client.request(
                        method, url, headers=self._headers(), **kwargs
                    )

                if resp.status_code == 204:
                    return {}

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue

                if resp.status_code >= 500:
                    if attempt < MAX_RETRIES - 1:
                        await self._sleep_with_backoff(attempt)
                        continue
                    raise ValueError(f"Server error {resp.status_code}: {resp.text}")

                if not resp.is_success:
                    try:
                        err_data = resp.json()
                        err_msg = err_data.get("detail", err_data.get("message", str(err_data)))
                    except Exception:
                        err_msg = resp.text[:200]
                    raise ValueError(f"HTTP {resp.status_code} {method} {endpoint}: {err_msg}")

                return resp.json()

            except httpx.TimeoutException as e:
                if attempt < MAX_RETRIES - 1:
                    await self._sleep_with_backoff(attempt)
                    continue
                raise ValueError(f"Timeout on {method} {endpoint}: {e}")

            except httpx.ConnectError as e:
                if attempt < MAX_RETRIES - 1:
                    await self._sleep_with_backoff(attempt)
                    continue
                raise ValueError(f"Connection error on {endpoint}: {e}")

        raise ValueError(f"Max retries exceeded for {method} {endpoint}")

    async def get(self, endpoint: str, **kwargs: Any) -> dict[str, Any] | list[dict[str, Any]]:
        return await self._request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, json: Any, **kwargs: Any) -> dict[str, Any]:
        return await self._request("POST", endpoint, json=json, **kwargs)

    async def patch(self, endpoint: str, json: Any, **kwargs: Any) -> dict[str, Any]:
        return await self._request("PATCH", endpoint, json=json, **kwargs)

    # --- Tags ---

    async def _get_or_create_tag_id(self, tag_name: str) -> int:
        """Resolve tag name to ID, creating if necessary."""
        if tag_name in self._tags_cache:
            return self._tags_cache[tag_name]

        data = await self.get("/tags", params={"type": "lead", "limit": 100})
        for tag in data.get("_embedded", {}).get("tags", []):
            if tag["name"] == tag_name:
                self._tags_cache[tag_name] = tag["id"]
                return tag["id"]

        created = await self.post("/tags", json=[{"name": tag_name, "type": "lead"}])
        tag = created.get("_embedded", {}).get("tags", [{}])[0]
        tag_id = tag.get("id", 0)
        if tag_id:
            self._tags_cache[tag_name] = tag_id
        return tag_id

    # --- Leads ---

    async def list_leads(
        self,
        pipeline_id: int | None = None,
        stage_id: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List leads with optional pipeline/stage filter."""
        params: dict[str, Any] = {"limit": min(limit, 100), "with": "contacts,tags"}
        if pipeline_id:
            params["filter[pipeline_id]"] = pipeline_id
        if stage_id and pipeline_id:
            params["filter[statuses][0][pipeline_id]"] = pipeline_id
            params["filter[statuses][0][status_id]"] = stage_id

        data = await self.get("/leads", params=params)
        leads = data.get("_embedded", {}).get("leads", [])

        if limit > 50:
            next_link = data.get("_links", {}).get("next")
            while next_link and len(leads) < limit:
                data = await self.get(next_link)
                batch = data.get("_embedded", {}).get("leads", [])
                leads.extend(batch)
                next_link = data.get("_links", {}).get("next")

        return leads[:limit]

    async def get_lead(self, lead_id: int) -> dict[str, Any]:
        return await self.get(
            f"/leads/{lead_id}", params={"with": "contacts,tags,custom_fields_values"}
        )

    async def create_lead(
        self,
        name: str,
        pipeline_id: int | None = None,
        stage_id: int | None = None,
        custom_fields: list[dict[str, Any]] | None = None,
        tags: list[str] | None = None,
        responsible_user_id: int | None = None,
        price: float | None = None,
    ) -> dict[str, Any]:
        """Create a new lead."""
        payload: dict[str, Any] = {"name": name}
        if pipeline_id:
            payload["pipeline_id"] = pipeline_id
        if stage_id:
            payload["status_id"] = stage_id
        if custom_fields:
            payload["custom_fields_values"] = custom_fields
        if responsible_user_id:
            payload["responsible_user_id"] = responsible_user_id
        if price is not None:
            payload["price"] = price
        if tags:
            tag_ids = [await self._get_or_create_tag_id(t) for t in tags]
            payload["_embedded"] = {"tags": [{"id": tid} for tid in tag_ids]}

        data = await self.post("/leads", json=[payload])
        return data.get("_embedded", {}).get("leads", [{}])[0]

    async def update_lead(self, lead_id: int, fields: dict[str, Any]) -> dict[str, Any]:
        return await self.patch(f"/leads/{lead_id}", json=fields)

    async def delete_lead(self, lead_id: int) -> dict[str, Any]:
        """Soft-delete: marks lead as deleted."""
        return await self.patch(f"/leads/{lead_id}", json={"is_deleted": True})

    async def move_lead_stage(
        self,
        lead_id: int,
        stage_id: int,
        pipeline_id: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"status_id": stage_id}
        if pipeline_id:
            payload["pipeline_id"] = pipeline_id
        return await self.patch(f"/leads/{lead_id}", json=payload)

    async def bulk_update_leads(self, leads_updates: list[dict[str, Any]]) -> dict[str, Any]:
        """Bulk update: 1 request for N leads."""
        payload = [{"id": u["id"], **u.get("fields", {})} for u in leads_updates]
        return await self.patch("/leads", json=payload)

    # --- Contacts ---

    async def list_contacts(
        self, query: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": min(limit, 100)}
        if query:
            params["query"] = query
        data = await self.get("/contacts", params=params)
        return data.get("_embedded", {}).get("contacts", [])

    async def get_contact(self, contact_id: int) -> dict[str, Any]:
        return await self.get(
            f"/contacts/{contact_id}", params={"with": "tags,custom_fields_values"}
        )

    async def create_contact(
        self,
        name: str,
        phone: str | None = None,
        email: str | None = None,
        custom_fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create contact with automatic phone/email field resolution."""
        payload: dict[str, Any] = {"name": name}
        cfv = list(custom_fields) if custom_fields else []

        if phone or email:
            fields = await self.list_custom_fields("contacts")
            field_map = {f["name"].upper(): f["id"] for f in fields}
            field_code_map = {f.get("code", "").upper(): f["id"] for f in fields}

            if phone:
                fid = field_map.get("PHONE") or field_code_map.get("PHONE")
                if fid:
                    cfv.append({"field_id": fid, "values": [{"value": phone, "enum_code": "WORK"}]})

            if email:
                fid = field_map.get("EMAIL") or field_code_map.get("EMAIL")
                if fid:
                    cfv.append({"field_id": fid, "values": [{"value": email, "enum_code": "WORK"}]})

        if cfv:
            payload["custom_fields_values"] = cfv

        data = await self.post("/contacts", json=[payload])
        return data.get("_embedded", {}).get("contacts", [{}])[0]

    async def update_contact(self, contact_id: int, fields: dict[str, Any]) -> dict[str, Any]:
        return await self.patch(f"/contacts/{contact_id}", json=fields)

    # --- Pipelines & Stages ---

    async def list_pipelines(self) -> list[dict[str, Any]]:
        cached = cache_get("pipelines")
        if cached is not None:
            return cached
        data = await self.get("/leads/pipelines")
        result = data.get("_embedded", {}).get("pipelines", [])
        cache_set("pipelines", result, ttl=600)
        return result

    async def create_pipeline(self, name: str) -> dict[str, Any]:
        cache_invalidate("pipelines")
        data = await self.post("/leads/pipelines", json=[{"name": name, "sort": 99}])
        return data.get("_embedded", {}).get("pipelines", [{}])[0]

    async def update_pipeline(self, pipeline_id: int, name: str) -> dict[str, Any]:
        cache_invalidate("pipelines")
        return await self.patch(f"/leads/pipelines/{pipeline_id}", json={"name": name})

    async def list_stages(self, pipeline_id: int) -> list[dict[str, Any]]:
        key = f"stages_{pipeline_id}"
        cached = cache_get(key)
        if cached is not None:
            return cached
        data = await self.get(f"/leads/pipelines/{pipeline_id}/statuses")
        result = data.get("_embedded", {}).get("statuses", [])
        cache_set(key, result, ttl=600)
        return result

    async def create_stage(
        self,
        pipeline_id: int,
        name: str,
        color: str | None = None,
    ) -> dict[str, Any]:
        cache_invalidate(f"stages_{pipeline_id}", "pipelines")
        existing = await self.list_stages(pipeline_id)
        editable = [s for s in existing if s.get("is_editable")]
        next_sort = max((s.get("sort", 0) for s in editable), default=10) + 10
        payload: dict[str, Any] = {"name": name, "sort": next_sort}
        if color:
            payload["color"] = color
        data = await self.post(f"/leads/pipelines/{pipeline_id}/statuses", json=[payload])
        return data.get("_embedded", {}).get("statuses", [{}])[0]

    async def update_stage(
        self,
        pipeline_id: int,
        stage_id: int,
        name: str | None = None,
        sort: int | None = None,
        color: str | None = None,
    ) -> dict[str, Any]:
        cache_invalidate(f"stages_{pipeline_id}", "pipelines")
        payload = {
            k: v
            for k, v in {"name": name, "sort": sort, "color": color}.items()
            if v is not None
        }
        return await self.patch(
            f"/leads/pipelines/{pipeline_id}/statuses/{stage_id}", json=payload
        )

    # --- Tags ---

    async def list_tags(self, entity_type: str = "lead") -> list[dict[str, Any]]:
        endpoint = f"/{entity_type}/tags"
        data = await self.get(endpoint, params={"limit": 100})
        return data.get("_embedded", {}).get("tags", [])

    async def add_tag(self, lead_id: int, tag_name: str) -> dict[str, Any]:
        tag_id = await self._get_or_create_tag_id(tag_name)
        lead = await self.get_lead(lead_id)
        existing = [t["id"] for t in lead.get("_embedded", {}).get("tags", [])]
        if tag_id not in existing:
            existing.append(tag_id)
        return await self.patch(
            f"/leads/{lead_id}",
            json={"_embedded": {"tags": [{"id": tid} for tid in existing]}},
        )

    async def remove_tag(self, lead_id: int, tag_name: str) -> dict[str, Any]:
        tag_id = await self._get_or_create_tag_id(tag_name)
        lead = await self.get_lead(lead_id)
        existing = [t["id"] for t in lead.get("_embedded", {}).get("tags", [])]
        updated = [tid for tid in existing if tid != tag_id]
        return await self.patch(
            f"/leads/{lead_id}",
            json={"_embedded": {"tags": [{"id": tid} for tid in updated]}},
        )

    # --- Tasks & Notes ---

    async def create_task(
        self,
        lead_id: int,
        text: str,
        due_date: int,
        responsible_user_id: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "text": text,
            "complete_till": due_date,
            "entity_id": lead_id,
            "entity_type": "leads",
            "task_type_id": 1,
        }
        if responsible_user_id:
            payload["responsible_user_id"] = responsible_user_id
        data = await self.post("/tasks", json=[payload])
        return data.get("_embedded", {}).get("tasks", [{}])[0]

    async def list_tasks(
        self,
        lead_id: int | None = None,
        filter_overdue: bool = False,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if lead_id:
            params["filter[entity_id]"] = lead_id
            params["filter[entity_type]"] = "leads"
        if filter_overdue:
            params["filter[complete_till][to]"] = int(time.time())
            params["filter[is_completed]"] = 0
        data = await self.get("/tasks", params=params)
        return data.get("_embedded", {}).get("tasks", [])

    async def add_note(self, lead_id: int, text: str) -> dict[str, Any]:
        payload = {"entity_id": lead_id, "note_type": "common", "params": {"text": text}}
        data = await self.post(f"/leads/{lead_id}/notes", json=[payload])
        return data.get("_embedded", {}).get("notes", [{}])[0]

    # --- Custom Fields ---

    async def list_custom_fields(self, entity_type: str = "leads") -> list[dict[str, Any]]:
        key = f"custom_fields_{entity_type}"
        cached = cache_get(key)
        if cached is not None:
            return cached
        data = await self.get(f"/{entity_type}/custom_fields")
        result = data.get("_embedded", {}).get("custom_fields", [])
        cache_set(key, result, ttl=3600)
        return result

    async def create_custom_field(
        self,
        entity_type: str,
        field_type: str,
        name: str,
        enum_values: list[str] | None = None,
    ) -> dict[str, Any]:
        cache_invalidate(f"custom_fields_{entity_type}")
        payload: dict[str, Any] = {"name": name, "type": field_type}
        if enum_values:
            payload["enums"] = [{"value": v, "sort": i * 10} for i, v in enumerate(enum_values)]
        data = await self.post(f"/{entity_type}/custom_fields", json=[payload])
        return data.get("_embedded", {}).get("custom_fields", [{}])[0]

    # --- Companies ---

    async def create_company(
        self,
        name: str,
        custom_fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name}
        if custom_fields:
            payload["custom_fields_values"] = custom_fields
        data = await self.post("/companies", json=[payload])
        return data.get("_embedded", {}).get("companies", [{}])[0]

    async def list_companies(self, limit: int = 50) -> list[dict[str, Any]]:
        data = await self.get("/companies", params={"limit": min(limit, 100)})
        return data.get("_embedded", {}).get("companies", [])

    # --- Leads Complex ---

    async def create_lead_complex(
        self,
        name: str,
        pipeline_id: int | None = None,
        stage_id: int | None = None,
        contact_name: str | None = None,
        contact_phone: str | None = None,
        contact_email: str | None = None,
        company_name: str | None = None,
        tags: list[str] | None = None,
        custom_fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create lead + contact + company in one call."""
        payload: dict[str, Any] = {"name": name}
        if pipeline_id:
            payload["pipeline_id"] = pipeline_id
        if stage_id:
            payload["status_id"] = stage_id
        if custom_fields:
            payload["custom_fields_values"] = custom_fields
        if tags:
            tag_ids = [await self._get_or_create_tag_id(t) for t in tags]
            payload["_embedded"] = {"tags": [{"id": tid} for tid in tag_ids]}

        if contact_name:
            contact: dict[str, Any] = {"name": contact_name}
            if contact_phone or contact_email:
                contact["custom_fields_values"] = []
                fields = await self.list_custom_fields("contacts")
                field_map = {f["name"].upper(): f["id"] for f in fields}
                field_code_map = {f.get("code", "").upper(): f["id"] for f in fields}

                if contact_phone:
                    fid = field_map.get("PHONE") or field_code_map.get("PHONE")
                    if fid:
                        contact["custom_fields_values"].append(
                            {"field_id": fid, "values": [{"value": contact_phone}]}
                        )
                if contact_email:
                    fid = field_map.get("EMAIL") or field_code_map.get("EMAIL")
                    if fid:
                        contact["custom_fields_values"].append(
                            {"field_id": fid, "values": [{"value": contact_email}]}
                        )
            payload["_embedded"] = payload.get("_embedded", {})
            payload["_embedded"]["contacts"] = [contact]

        if company_name:
            payload["_embedded"] = payload.get("_embedded", {})
            payload["_embedded"]["companies"] = [{"name": company_name}]

        data = await self.post("/leads/complex", json=[payload])
        return data.get("_embedded", {}).get("leads", [{}])[0]

    # --- Chat ---

    async def list_chat_templates(self) -> list[dict[str, Any]]:
        data = await self.get("/chats/templates")
        return data.get("_embedded", {}).get("chat_templates", [])

    async def send_chat_message(self, lead_id: int, text: str) -> dict[str, Any]:
        data = await self.get("/talks", params={"filter[lead_id]": lead_id, "limit": 1})
        talks = data.get("_embedded", {}).get("talks", [])
        if not talks:
            raise ValueError(f"No active conversation for lead {lead_id}")
        talk_id = talks[0]["id"]
        return await self.post(
            f"/talks/{talk_id}/messages", json=[{"text": text, "type": "outgoing"}]
        )
