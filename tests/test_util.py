from __future__ import annotations

from wealthbox_tools.cli._util import build_linked_to


def _as_dicts(refs):
    return [r.model_dump() for r in refs]


def test_build_linked_to_all_none() -> None:
    assert build_linked_to(None, None, None) is None


def test_build_linked_to_contact_only() -> None:
    result = build_linked_to(123, None, None)
    assert _as_dicts(result) == [{"id": 123, "type": "Contact"}]


def test_build_linked_to_project_only() -> None:
    result = build_linked_to(None, 456, None)
    assert _as_dicts(result) == [{"id": 456, "type": "Project"}]


def test_build_linked_to_opportunity_only() -> None:
    result = build_linked_to(None, None, 789)
    assert _as_dicts(result) == [{"id": 789, "type": "Opportunity"}]


def test_build_linked_to_contact_and_project() -> None:
    result = build_linked_to(123, 456, None)
    assert _as_dicts(result) == [
        {"id": 123, "type": "Contact"},
        {"id": 456, "type": "Project"},
    ]


def test_build_linked_to_all_three() -> None:
    result = build_linked_to(1, 2, 3)
    assert _as_dicts(result) == [
        {"id": 1, "type": "Contact"},
        {"id": 2, "type": "Project"},
        {"id": 3, "type": "Opportunity"},
    ]
