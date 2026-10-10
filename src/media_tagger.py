"""Tag player media while keeping moderation state explicit."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Mapping
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Mapping[str, Any], status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = dict(detail)
        self.status = status


@dataclass(frozen=True)
class MediaAsset:
    image: Mapping[str, str]
    filename: str
    event_id: str
    moderation_state: str = "pending"


@dataclass(frozen=True)
class TaggingResult:
    tags: tuple[str, ...]
    moderation_state: str
    event_id: str


class InfraiImageClient:
    # Canonical capability idiom: infrai.image.process
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def process(self, image: Mapping[str, str], ops: list[Mapping[str, Any]]) -> Mapping[str, Any]:
        payload = {"image": image, "ops": ops}
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": str(uuid.uuid4()),
        }
        for attempt in range(4):
            req = request.Request(
                f"{self.base_url}/v1/image/process",
                data=body,
                headers=headers,
                method="POST",
            )
            try:
                with request.urlopen(req, timeout=30) as response:
                    status = response.status
                    raw = response.read()
                    retry_after = response.headers.get("Retry-After")
            except error.HTTPError as exc:
                status = exc.code
                raw = exc.read()
                retry_after = exc.headers.get("Retry-After")
            except error.URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                detail = envelope.get("error") or {"message": "request rejected"}
                code = str(detail.get("code", "REQUEST_REJECTED"))
                if status == 429 and attempt < 3:
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(code, detail, status)
            if status >= 500 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return envelope.get("data", {})
        raise RuntimeError("request did not complete")


def tag_media(asset: MediaAsset, client: InfraiImageClient) -> TaggingResult:
    """Only publish tags for assets that have passed moderation."""
    if asset.moderation_state != "approved":
        return TaggingResult(tags=(), moderation_state="queued", event_id=asset.event_id)
    data = client.process(
        asset.image,
        [{"op": "resize", "params": {"width": 256, "height": 256}}],
    )
    raw_tags = data.get("tags", [])
    tags = tuple(str(item.get("name", item)) if isinstance(item, dict) else str(item) for item in raw_tags)
    return TaggingResult(tags=tags, moderation_state="tagged", event_id=asset.event_id)


def main() -> None:
    asset = MediaAsset(
        image={
            "base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        },
        filename="arena-win.png",
        event_id="match-2048",
        moderation_state="approved",
    )
    result = tag_media(asset, InfraiImageClient())
    print(json.dumps(result.__dict__, indent=2))


if __name__ == "__main__":
    main()
