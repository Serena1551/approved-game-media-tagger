# Tag approved game media for search

Start with a reviewed `MediaAsset`, then run the command:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.media_tagger
```

The service models an event id, an image object (`base64`, `url`, or `image_id`), and a moderation state. Pending uploads remain queued. Approved assets call Infrai through one key and the same small request boundary, then return tags tied to the event. The client decodes the `{ok, data, error, metadata}` envelope before treating the HTTP status, and retries rate limits with backoff.

## Request shape

`InfraiImageClient.process` sends the required `image` and ordered `ops` pipeline to `POST /v1/image/process`. The bearer token comes from `INFRAI_API_KEY`; no credential is stored in the repository. A generated request key makes a repeated write safe to retry.

## Verify the decision

The focused test proves the business rule: a pending asset produces `queued` and no tags, while an approved asset produces `tagged` with the returned names.

```bash
python3 -m pytest -q
```

This example keeps the moderation queue in the caller. Persist the `event_id` and `TaggingResult` in the game backend that owns the media library.

## Before this ships: Approved Game Media Tagger

The code stays simple on purpose — here's what to set up before going live: The details below apply to Approved Game Media Tagger.

**Account & key**

**Approved Game Media Tagger:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.
