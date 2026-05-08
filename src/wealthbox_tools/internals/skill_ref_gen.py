"""Skill-reference markdown auto-generator.

The wealthbox-crm skill ships per-resource reference markdown files under
``src/wealthbox_tools/skills/wealthbox-crm/references/``. Each file contains
hand-written editorial content (intro, examples, tips) interleaved with
flag tables that must stay in lock-step with the Typer command surface.

This module owns the flag tables. They are delimited in markdown by HTML
comment markers so they survive markdown renderers without artifacts:

    <!-- auto-gen:flags -->
    ...generated content...
    <!-- /auto-gen:flags -->

``regenerate_all()`` walks the live Typer command tree, looks up the
markdown file for each top-level resource in :data:`RESOURCE_REFERENCE_MAP`,
and rewrites everything between the markers. Editorial content outside the
markers is never touched. Files lacking the markers are left alone with a
one-line warning to stderr.

The output is **deterministic**: commands and flags are sorted, choice
lists are sorted, and a regenerated tree produces a byte-identical diff on
a second pass.
"""
from __future__ import annotations

import enum
import sys
from dataclasses import dataclass, field
from pathlib import Path

import click
import typer

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

OPEN_MARKER = "<!-- auto-gen:flags -->"
CLOSE_MARKER = "<!-- /auto-gen:flags -->"


@dataclass
class ChangeSet:
    """Result of a regeneration pass.

    ``modified`` lists absolute paths of files whose contents changed on
    disk. ``skipped_no_markers`` lists paths that exist but lack the
    auto-gen markers (a warning was already printed to stderr). ``missing``
    lists paths that were expected but not found on disk.
    """

    modified: list[Path] = field(default_factory=list)
    skipped_no_markers: list[Path] = field(default_factory=list)
    missing: list[Path] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Resource → markdown file mapping
# ---------------------------------------------------------------------------

#: Top-level Typer sub-app name → reference markdown filename (relative to
#: the references directory). Slice #30 covers `contacts` only; subsequent
#: issues will extend this map.
RESOURCE_REFERENCE_MAP: dict[str, str] = {
    "contacts": "contacts.md",
}


def _references_dir() -> Path:
    """Return the absolute path to the references/ directory in this checkout."""
    # internals/ is a sibling of skills/. Walk up to the wealthbox_tools
    # package root and then into the skill's references dir.
    return (
        Path(__file__).resolve().parent.parent
        / "skills"
        / "wealthbox-crm"
        / "references"
    )


# ---------------------------------------------------------------------------
# Click introspection
# ---------------------------------------------------------------------------

@dataclass
class FlagInfo:
    """A single CLI flag, normalised for rendering.

    All fields are pre-formatted strings except ``choices`` which carries
    the sorted list of valid enum values (empty for non-enum flags).
    """

    primary: str          # e.g. "--first-name"
    aliases: tuple[str, ...]  # e.g. ("-v",) — sorted, primary excluded
    type_label: str       # e.g. "TEXT", "INTEGER", "BOOLEAN", "Gender"
    description: str      # Typer help text, single-line
    default: str          # rendered default ("-" when no default)
    choices: tuple[str, ...]  # sorted enum values, empty if not an enum


@dataclass
class CommandInfo:
    """A single CLI command and its flags."""

    path: tuple[str, ...]      # ("contacts", "add", "person")
    synopsis: str              # one-line help/short_help
    flags: tuple[FlagInfo, ...]


def _is_hidden(cmd: click.Command) -> bool:
    return bool(getattr(cmd, "hidden", False))


def _walk_commands(
    cmd: click.Command,
    path: tuple[str, ...] = (),
) -> list[CommandInfo]:
    """Recursively collect non-hidden leaf commands from a Click command tree."""
    if _is_hidden(cmd):
        return []
    if isinstance(cmd, click.Group):
        out: list[CommandInfo] = []
        # Sort sub-command names for determinism.
        for name in sorted(cmd.commands):
            sub = cmd.commands[name]
            out.extend(_walk_commands(sub, path + (name,)))
        return out
    return [_describe_command(cmd, path)]


def _describe_command(cmd: click.Command, path: tuple[str, ...]) -> CommandInfo:
    synopsis = (cmd.short_help or cmd.help or "").strip().splitlines()
    synopsis_line = synopsis[0] if synopsis else ""

    flags: list[FlagInfo] = []
    for param in cmd.params:
        if not isinstance(param, click.Option):
            # Arguments are documented in the command synopsis, not the
            # flag table.
            continue
        if param.hidden:
            continue
        flags.append(_describe_option(param))

    # Sort flags alphabetically by primary flag name (case-insensitive),
    # so the rendered table is deterministic.
    flags.sort(key=lambda f: f.primary.lstrip("-").lower())
    return CommandInfo(path=path, synopsis=synopsis_line, flags=tuple(flags))


def _describe_option(opt: click.Option) -> FlagInfo:
    long_opts = sorted([o for o in opt.opts if o.startswith("--")])
    short_opts = sorted([o for o in opt.opts if o.startswith("-") and not o.startswith("--")])
    if long_opts:
        primary = long_opts[0]
        rest_long = tuple(long_opts[1:])
    elif short_opts:
        primary = short_opts[0]
        rest_long = ()
    else:
        primary = (opt.opts or ["?"])[0]
        rest_long = ()

    # Boolean negation flags ("--active/--inactive") show up in
    # secondary_opts on Click; surface them as aliases so the doc reflects
    # the negative form.
    sec = sorted(getattr(opt, "secondary_opts", []) or [])

    aliases = tuple(sorted(set(rest_long + tuple(short_opts) + tuple(sec)) - {primary}))

    type_label, choices = _render_type(opt)
    default = _render_default(opt)
    description = (opt.help or "").strip().replace("\n", " ")
    if description:
        # Collapse runs of whitespace introduced by the newline replacement.
        description = " ".join(description.split())

    return FlagInfo(
        primary=primary,
        aliases=aliases,
        type_label=type_label,
        description=description,
        default=default,
        choices=tuple(choices),
    )


def _render_type(opt: click.Option) -> tuple[str, list[str]]:
    """Return (type_label, sorted_enum_choices)."""
    pt = opt.type
    if isinstance(pt, click.Choice):
        # Typer renders enum-typed Options via click.Choice.
        choices = sorted(str(c) for c in pt.choices)
        # Use a stable label distinct from raw "Choice" so readers can tell
        # at a glance that this is an enum-bounded flag.
        return ("CHOICE", choices)
    if opt.is_flag or opt.count:
        return ("BOOLEAN", [])
    # Map common Click param types to the labels Typer prints.
    name = getattr(pt, "name", None) or pt.__class__.__name__
    label_map = {
        "text": "TEXT",
        "integer": "INTEGER",
        "boolean": "BOOLEAN",
        "float": "FLOAT",
    }
    return (label_map.get(name, name.upper()), [])


def _render_default(opt: click.Option) -> str:
    """Render the option default deterministically."""
    if not opt.show_default and opt.default is None:
        return "-"
    default = opt.default
    if callable(default):
        try:
            default = default()
        except Exception:  # pragma: no cover - defensive
            default = None
    if default is None:
        return "-"
    if isinstance(default, bool):
        return "true" if default else "false"
    if isinstance(default, enum.Enum):
        return str(default.value)
    if isinstance(default, (list, tuple)):
        if not default:
            return "-"
        return ", ".join(str(x) for x in default)
    return str(default)


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _render_block(commands: list[CommandInfo]) -> str:
    """Render the body that lives between the auto-gen markers.

    Output ends with a newline so a regenerated file ends cleanly. The
    block is deterministic for a given input.
    """
    if not commands:
        return ""
    # Sort commands by full path for stable ordering.
    commands = sorted(commands, key=lambda c: c.path)

    chunks: list[str] = []
    for cmd in commands:
        chunks.append(_render_command(cmd))
    # Single blank line between commands; trailing newline at the end.
    return "\n".join(chunks).rstrip() + "\n"


def _render_command(cmd: CommandInfo) -> str:
    invocation = "wbox " + " ".join(cmd.path)
    lines: list[str] = []
    lines.append(f"### `{invocation}`")
    lines.append("")
    if cmd.synopsis:
        lines.append(cmd.synopsis)
        lines.append("")

    if not cmd.flags:
        lines.append("_No flags._")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Flag | Type | Default | Description |")
    lines.append("|------|------|---------|-------------|")
    enum_blocks: list[str] = []
    for flag in cmd.flags:
        flag_cell = f"`{flag.primary}`"
        if flag.aliases:
            flag_cell += " / " + " / ".join(f"`{a}`" for a in flag.aliases)
        type_cell = f"`{flag.type_label}`"
        default_cell = f"`{flag.default}`"
        desc_cell = _escape_table_cell(flag.description) or ""
        lines.append(f"| {flag_cell} | {type_cell} | {default_cell} | {desc_cell} |")
        if flag.choices:
            block = [f"**Choices for `{flag.primary}`:**", ""]
            block.extend(f"- `{c}`" for c in flag.choices)
            block.append("")
            enum_blocks.append("\n".join(block))

    lines.append("")
    if enum_blocks:
        lines.extend(enum_blocks)

    return "\n".join(lines).rstrip() + "\n"


def _escape_table_cell(text: str) -> str:
    """Escape a description so it survives a markdown pipe-table cell."""
    return text.replace("|", "\\|")


# ---------------------------------------------------------------------------
# File rewriting
# ---------------------------------------------------------------------------

def _rewrite_between_markers(content: str, new_block: str) -> str | None:
    """Replace the content between the auto-gen markers.

    Returns the rewritten content, or ``None`` if the markers are not
    present (or are malformed) so the caller can warn and skip.
    """
    open_idx = content.find(OPEN_MARKER)
    if open_idx == -1:
        return None
    close_idx = content.find(CLOSE_MARKER, open_idx + len(OPEN_MARKER))
    if close_idx == -1:
        return None

    # Preserve everything up to and including the open marker line, replace
    # the body, then resume at the close marker line. We always leave
    # exactly one newline after the open marker and one blank line before
    # the close marker to keep the diff stable.
    before = content[: open_idx + len(OPEN_MARKER)]
    after = content[close_idx:]

    body = new_block.strip("\n")
    if body:
        middle = "\n" + body + "\n"
    else:
        middle = "\n"

    return before + middle + after


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def _collect_commands_for_resource(resource: str) -> list[CommandInfo]:
    """Return the leaf commands rooted at ``wbox <resource>``.

    Raises:
        KeyError: if ``resource`` is not registered under the root Typer app.
            This catches typos and stale entries in
            :data:`RESOURCE_REFERENCE_MAP` before we silently overwrite a
            reference file with an empty flag block.
    """
    from wealthbox_tools.cli.main import app as _root_app

    click_root = typer.main.get_command(_root_app)
    if not isinstance(click_root, click.Group):  # pragma: no cover - sanity
        return []
    sub = click_root.commands.get(resource)
    if sub is None:
        raise KeyError(
            f"skill-ref auto-gen: resource {resource!r} is mapped in "
            "RESOURCE_REFERENCE_MAP but not registered on the root Typer app. "
            "Fix the map entry or register the sub-app before regenerating."
        )
    return _walk_commands(sub, path=(resource,))


def regenerate_all(*, references_dir: Path | None = None) -> ChangeSet:
    """Regenerate every reference markdown file we know how to drive.

    For each entry in :data:`RESOURCE_REFERENCE_MAP`, walk the Typer command
    tree under that top-level resource, render the auto-gen block, and
    write it into the corresponding markdown file between the auto-gen
    markers. Editorial content outside the markers is preserved.

    A file lacking the markers is left untouched and a one-line warning is
    printed to stderr (it is recorded in :class:`ChangeSet.skipped_no_markers`).
    Files listed in the map but missing on disk are recorded in
    :class:`ChangeSet.missing` and skipped silently — adding the file is the
    operator's job.
    """
    refs_dir = references_dir or _references_dir()
    changeset = ChangeSet()

    # Sort for deterministic warning order.
    for resource in sorted(RESOURCE_REFERENCE_MAP):
        target = refs_dir / RESOURCE_REFERENCE_MAP[resource]
        if not target.exists():
            changeset.missing.append(target)
            continue
        original = target.read_text(encoding="utf-8")

        commands = _collect_commands_for_resource(resource)
        new_block = _render_block(commands)
        rewritten = _rewrite_between_markers(original, new_block)
        if rewritten is None:
            print(
                f"warning: skill-ref auto-gen markers not found in {target}; "
                "leaving file unchanged",
                file=sys.stderr,
            )
            changeset.skipped_no_markers.append(target)
            continue
        if rewritten != original:
            target.write_text(rewritten, encoding="utf-8")
            changeset.modified.append(target)

    return changeset
