"""Backwards-compatible re-export shim for the CLI utility helpers.

The implementation now lives in four focused modules:

- ``_client`` — token resolution, client lifecycle, error handling.
- ``_format`` — output formatting, comment shaping, truncation/HTML helpers.
- ``_resolve`` — id/name resolution, linked_to / resource-filter builders, more-fields parsing.
- ``_factory`` — Typer app + category command factories.

Every public name this module historically exported is re-exported here so that
``from ._util import ...`` continues to work unchanged across the CLI modules.
"""
from __future__ import annotations

from ._client import (
    get_client,
    handle_errors,
    run_client,
    run_client_with_comments,
)
from ._factory import (
    COMMENT_RESOURCE_TYPES,
    _GetShortcutGroup,
    make_category_command,
    make_resource_app,
)
from ._format import (
    _COMMENT_PREVIEW_LEN,
    _SLIM_COMMENT_FIELDS,
    OutputFormat,
    _extract_collection,
    _filter_fields,
    _flatten_record,
    _flatten_value,
    _render_dsv,
    _render_kv_table,
    _render_table,
    _strip_html,
    _strip_html_keys,
    clean_comments,
    output_get_result,
    output_result,
    slim_comments,
    summarize_comments,
    truncate_field,
    truncate_nested_field,
)
from ._resolve import (
    _match_contact_role,
    _match_role_option,
    _role_option_user,
    active_to_status,
    build_linked_to,
    build_resource_filter,
    parse_more_fields,
    resolve_category_id,
    resolve_contact_roles,
)

__all__ = [
    "COMMENT_RESOURCE_TYPES",
    "OutputFormat",
    "_COMMENT_PREVIEW_LEN",
    "_GetShortcutGroup",
    "_SLIM_COMMENT_FIELDS",
    "_extract_collection",
    "_filter_fields",
    "_flatten_record",
    "_flatten_value",
    "_match_contact_role",
    "_match_role_option",
    "_render_dsv",
    "_render_kv_table",
    "_render_table",
    "_role_option_user",
    "_strip_html",
    "_strip_html_keys",
    "active_to_status",
    "build_linked_to",
    "build_resource_filter",
    "clean_comments",
    "get_client",
    "handle_errors",
    "make_category_command",
    "make_resource_app",
    "output_get_result",
    "output_result",
    "parse_more_fields",
    "resolve_category_id",
    "resolve_contact_roles",
    "run_client",
    "run_client_with_comments",
    "slim_comments",
    "summarize_comments",
    "truncate_field",
    "truncate_nested_field",
]
