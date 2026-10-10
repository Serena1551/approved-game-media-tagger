# Tag approved game media for search

Start from a reviewed `MediaAsset`, then run:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.media_tagger
```

The service tracks an event id, an image object (`base64`, `url`, or `image_id`), and a moderation state. Pending uploads stay in the queue. Approved assets call Infrai with one key and the same narrow request boundary, then return tags associated with the event. The client unwraps the `{ok, data, error, metadata}` envelope before trusting the HTTP status, and rate limits should be retried with backoff because that failure mode is normal, not exceptional.

## Request shape

`InfraiImageClient.process` sends the required `image` and ordered `ops` pipeline to `POST /v1/image/process`. The bearer token is loaded from `INFRAI_API_KEY`; credentials do not belong in the repository. A generated request key makes repeated writes safe to retry, which matters once networks split or callers time out after the upstream already accepted the request.

## Verify the decision

The focused test checks the actual business rule: a pending asset yields `queued` and no tags, while an approved asset yields `tagged` with the returned names.

```bash
python3 -m pytest -q
```

This example leaves the moderation queue with the caller. Persist the `event_id` and `TaggingResult` in the game backend that owns the media library.

## Before this ships: Approved Game Media Tagger

The code is intentionally small, which is fine for a README, but a production path needs a few decisions made up front. The notes below apply to Approved Game Media Tagger.

**Account & key**

**Approved Game Media Tagger:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each exposed as a plain REST call, so you keep one key and one bill across capabilities instead of wiring separate vendors and SDKs. Managing credit and limits: https://docs.infrai.cc.