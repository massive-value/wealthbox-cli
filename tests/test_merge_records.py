"""`merge_records_by_id` — the de-duplication behind the "all" list variants."""
from __future__ import annotations

from wealthbox_tools.client.base import merge_records_by_id


def test_disjoint_batches_concatenate_in_order() -> None:
    merged = merge_records_by_id([[{"id": 1}, {"id": 2}], [{"id": 3}]])
    assert [r["id"] for r in merged] == [1, 2, 3]


def test_later_updated_at_wins_across_timezones() -> None:
    """Wealthbox stamps are "2025-05-24 10:00 AM -0400" — not string-sortable.
    09:00 -0700 (16:00 UTC) is later than 10:00 -0400 (14:00 UTC)."""
    old = {"id": 1, "updated_at": "2025-05-24 10:00 AM -0400", "v": "old"}
    new = {"id": 1, "updated_at": "2025-05-24 09:00 AM -0700", "v": "new"}
    assert merge_records_by_id([[old], [new]])[0]["v"] == "new"
    assert merge_records_by_id([[new], [old]])[0]["v"] == "new"


def test_iso_timestamps_are_understood_too() -> None:
    old = {"id": 1, "updated_at": "2025-05-24T10:00:00-04:00", "v": "old"}
    new = {"id": 1, "updated_at": "2025-05-24T12:00:00-04:00", "v": "new"}
    assert merge_records_by_id([[old], [new]])[0]["v"] == "new"


def test_unparseable_timestamp_never_displaces_a_real_one() -> None:
    good = {"id": 1, "updated_at": "2025-05-24 10:00 AM -0400", "v": "good"}
    junk = {"id": 1, "updated_at": "whenever", "v": "junk"}
    assert merge_records_by_id([[good], [junk]])[0]["v"] == "good"
    assert merge_records_by_id([[junk], [good]])[0]["v"] == "good"


def test_records_without_an_id_are_kept() -> None:
    merged = merge_records_by_id([[{"id": 1}], [{"name": "no id"}]])
    assert len(merged) == 2


def test_empty_input() -> None:
    assert merge_records_by_id([]) == []
    assert merge_records_by_id([[], []]) == []
