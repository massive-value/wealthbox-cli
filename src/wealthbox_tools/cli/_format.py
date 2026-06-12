from __future__ import annotations

import csv
import io
import json
import os
from enum import StrEnum
from typing import Any

import typer

_COMMENT_PREVIEW_LEN = 50
_SLIM_COMMENT_FIELDS = ("updated_at", "created_at", "creator")


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode common HTML entities."""
    import html
    import re
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def clean_comments(data: dict[str, Any]) -> dict[str, Any]:
    """Strip HTML from body.text in each comment, keeping full structure (for verbose output)."""
    comments = data.get("comments")
    if not isinstance(comments, list):
        return data
    cleaned = []
    for c in comments:
        body = c.get("body")
        if isinstance(body, dict) and "text" in body:
            c = {**c, "body": {**body, "text": _strip_html(body["text"])}}
        cleaned.append(c)
    return {**data, "comments": cleaned}


def slim_comments(data: dict[str, Any]) -> dict[str, Any]:
    """Strip HTML, trim to essential fields, and unnest body.text → text (single pass)."""
    comments = data.get("comments")
    if not isinstance(comments, list):
        return data
    slimmed = []
    for c in comments:
        entry = {k: c[k] for k in _SLIM_COMMENT_FIELDS if k in c}
        body = c.get("body")
        raw = body.get("text", "") if isinstance(body, dict) else str(body or "")
        entry["text"] = _strip_html(raw)
        slimmed.append(entry)
    return {**data, "comments": slimmed}


def summarize_comments(data: dict[str, Any]) -> dict[str, Any]:
    """Replace a ``comments`` list with ``comment_count`` and ``latest_comment`` summary fields."""
    comments = data.get("comments")
    if comments is None:
        return data
    data = {k: v for k, v in data.items() if k != "comments"}
    data["comment_count"] = len(comments)
    if comments:
        newest = max(comments, key=lambda c: c.get("created_at", c.get("updated_at", "")))
        text = newest.get("text", "")
        preview = text[:_COMMENT_PREVIEW_LEN] + "..." if len(text) > _COMMENT_PREVIEW_LEN else text
        data["latest_comment"] = preview
    else:
        data["latest_comment"] = ""
    return data


def output_get_result(
    result: dict[str, Any], fmt: OutputFormat, fields: list[str] | None = None
) -> None:
    """Standard output pipeline for get commands with comments: slim → summarize → output."""
    result = slim_comments(result)
    if fmt != OutputFormat.JSON:
        result = summarize_comments(result)
    output_result(result, fmt, fields=fields)


class OutputFormat(StrEnum):
    JSON = "json"
    TABLE = "table"
    CSV = "csv"
    TSV = "tsv"


def _filter_fields(data: Any, fields: list[str]) -> Any:
    if isinstance(data, list):
        return [{f: item[f] for f in fields if f in item} for item in data]
    if isinstance(data, dict):
        if "meta" in data:
            return {
                k: ([{f: item[f] for f in fields if f in item} for item in v] if isinstance(v, list) else v)
                for k, v in data.items()
            }
        return {f: data[f] for f in fields if f in data}
    return data


def truncate_nested_field(data: Any, parent: str, fields: list[str], max_len: int) -> Any:
    """Truncate one or more string fields nested inside a dict field in each item of a response."""
    def _trim(item: Any) -> Any:
        if not (isinstance(item, dict) and isinstance(item.get(parent), dict)):
            return item
        nested = item[parent]
        updates = {
            f: nested[f][:max_len] + "..."
            for f in fields
            if f in nested and isinstance(nested[f], str) and len(nested[f]) > max_len
        }
        if updates:
            item = {**item, parent: {**nested, **updates}}
        return item

    if isinstance(data, list):
        return [_trim(item) for item in data]
    if isinstance(data, dict):
        return {k: [_trim(i) for i in v] if isinstance(v, list) else v for k, v in data.items()}
    return _trim(data)


def truncate_field(data: Any, field: str, max_len: int) -> Any:
    """Truncate a string field in each item of a response to max_len characters."""
    def _trim(item: Any) -> Any:
        if isinstance(item, dict) and field in item and isinstance(item[field], str):
            if len(item[field]) > max_len:
                item = {**item, field: item[field][:max_len] + "..."}
        return item

    if isinstance(data, list):
        return [_trim(item) for item in data]
    if isinstance(data, dict):
        return {k: [_trim(i) for i in v] if isinstance(v, list) else v for k, v in data.items()}
    return _trim(data)


def _flatten_value(value: Any) -> Any:
    """Convert a single field value to a scalar suitable for tabular display."""
    if value is None:
        return ""
    if isinstance(value, list):
        if not value:
            return ""
        first = value[0]
        if isinstance(first, str):
            # e.g. tags: ["VIP", "Prospect"]
            return ", ".join(str(v) for v in value)
        if isinstance(first, dict):
            if "address" in first:
                # e.g. email_addresses, phone_numbers — return principal's address
                for item in value:
                    if item.get("principal"):
                        return item["address"]
                return first["address"]
            if "id" in first and "type" in first:
                # e.g. linked_to, invitees — prefer name if available
                parts = []
                for item in value:
                    name = item.get("name")
                    parts.append(name if name else f"{item['type']}:{item['id']}")
                return ", ".join(parts)
            return f"[{len(value)} items]"
    if isinstance(value, dict):
        return json.dumps(value)
    return value


def _flatten_record(record: dict[str, Any]) -> dict[str, Any]:
    return {k: _flatten_value(v) for k, v in record.items()}


def _extract_collection(data: Any) -> tuple[list[dict[str, Any]] | None, int | None]:
    """Return (rows, total_count) or (None, None) for a single-object response."""
    if isinstance(data, list):
        return data, None
    if isinstance(data, dict):
        if "meta" in data:
            rows: list[dict[str, Any]] = []
            for k, v in data.items():
                if k != "meta" and isinstance(v, list):
                    rows = v
                    break
            total = data["meta"].get("total_count") or data["meta"].get("total_entries")
            return rows, total
        # Check if any value is a list (collection without meta).
        # Skip when the dict looks like a single resource (has an "id" key) —
        # nested lists like linked_to, subtasks, comments are not collections.
        if "id" not in data:
            for v in data.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    return v, None
    return None, None


def _render_table(rows: list[dict[str, Any]], headers: list[str], total_count: int | None) -> tuple[str, str | None]:
    from tabulate import tabulate
    table_data = [[row.get(h, "") for h in headers] for row in rows]
    rendered = tabulate(table_data, headers=headers, tablefmt="grid")
    footer = f"Showing {len(rows)} of {total_count} results" if total_count is not None else None
    return rendered, footer


def _render_kv_table(record: dict[str, Any]) -> str:
    from tabulate import tabulate
    return tabulate(list(record.items()), headers=["Field", "Value"], tablefmt="grid")


def _render_dsv(rows: list[dict[str, Any]], headers: list[str], sep: str) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=sep)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(h, "") for h in headers])
    return buf.getvalue()


def _strip_html_keys(data: Any) -> Any:
    """Recursively remove dict keys ending in `_html`."""
    if isinstance(data, dict):
        return {
            k: _strip_html_keys(v)
            for k, v in data.items()
            if not (isinstance(k, str) and k.endswith("_html"))
        }
    if isinstance(data, list):
        return [_strip_html_keys(item) for item in data]
    return data


def output_result(data: Any, fmt: OutputFormat = OutputFormat.JSON, fields: list[str] | None = None) -> None:
    """Print result to stdout in the requested format."""
    # Project before stripping so we don't recurse into fields we're dropping anyway.
    if fields is not None:
        data = _filter_fields(data, fields)
    if os.environ.get("WBOX_BRIEF"):
        data = _strip_html_keys(data)
    if fmt == OutputFormat.JSON:
        typer.echo(json.dumps(data, indent=2, default=str))
        return

    # Tabular formats
    sep = "\t" if fmt == OutputFormat.TSV else ","
    rows, total_count = _extract_collection(data)
    if rows is None:
        # Single object
        record = _flatten_record(data if isinstance(data, dict) else {"value": data})
        if fmt == OutputFormat.TABLE:
            typer.echo(_render_kv_table(record))
        else:
            typer.echo(_render_dsv([record], list(record.keys()), sep), nl=False)
    else:
        flat_rows = [_flatten_record(r) for r in rows]
        headers = list(flat_rows[0].keys()) if flat_rows else []
        if fmt == OutputFormat.TABLE:
            rendered, footer = _render_table(flat_rows, headers, total_count)
            typer.echo(rendered)
            if footer:
                typer.echo(footer, err=True)
        else:
            typer.echo(_render_dsv(flat_rows, headers, sep), nl=False)
