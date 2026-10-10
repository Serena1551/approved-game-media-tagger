from src.media_tagger import InfraiImageClient, MediaAsset, tag_media


class StubClient(InfraiImageClient):
    def __init__(self):
        pass

    def process(self, image: dict[str, str], ops: list[dict]):
        return {"tags": [{"name": "tournament"}, {"name": "victory-screen"}]}


def test_pending_asset_stays_in_queue_without_calling_api():
    result = tag_media(
        MediaAsset({"image_id": "img-ref"}, "match.png", "event-7", moderation_state="pending"),
        StubClient(),
    )
    assert result.moderation_state == "queued"
    assert result.tags == ()


def test_approved_asset_gets_search_tags():
    result = tag_media(
        MediaAsset({"image_id": "img-ref"}, "match.png", "event-7", moderation_state="approved"),
        StubClient(),
    )
    assert result.moderation_state == "tagged"
    assert result.tags == ("tournament", "victory-screen")
