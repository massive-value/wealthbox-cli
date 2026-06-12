from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import typer
from typer.core import TyperGroup

from wealthbox_tools.models import CategoryListQuery, CategoryType

from ._client import handle_errors, run_client, run_client_with_comments
from ._format import OutputFormat, output_get_result, output_result

if TYPE_CHECKING:
    # click is only referenced in type annotations below; importing it at
    # runtime would crash on installs where typer (>=0.26) does not pull in
    # click. Keep it type-only. See the 2.3.1 fix for the same class of bug.
    import click


class _GetShortcutGroup(TyperGroup):
    """Typer Group that routes numeric first arguments to the ``get`` subcommand."""

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        if args and args[0].isdigit() and args[0] not in self.commands:
            args.insert(0, "get")
        return super().resolve_command(ctx, args)


def make_resource_app(*, help: str) -> typer.Typer:
    """Create a Typer app that supports ``wbox <resource> <id>`` as shorthand for ``get <id>``."""
    return typer.Typer(
        cls=_GetShortcutGroup,
        context_settings={"help_option_names": ["-h", "--help"]},
        help=help,
        no_args_is_help=True,
    )


# Maps CLI resource names to the CommentResourceType string expected by GET /comments
COMMENT_RESOURCE_TYPES: dict[str, str] = {
    "tasks": "Task",
    "events": "Event",
    "notes": "StatusUpdates",
    "opportunities": "Opportunity",
    "projects": "Project",
    "workflows": "Workflow",
}


def make_category_command(category_type: CategoryType) -> Callable[..., None]:
    """Factory that returns a Typer command function for listing a category type."""
    @handle_errors
    def cmd(
        page: int | None = typer.Option(None, help="Page number"),
        per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
        token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
        fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
    ) -> None:
        query = CategoryListQuery(page=page, per_page=per_page)
        output_result(run_client(token, lambda c: c.list_categories(category_type, query)), fmt)
    return cmd


# ---------------------------------------------------------------------------
# Resource-command factory
# ---------------------------------------------------------------------------
#
# ``create_resource_commands`` generates the standard CRUD command set for a
# resource onto its Typer app from a :class:`ResourceSpec`.
#
# Two classes of command:
#
# * ``get`` and ``delete`` are *fully mechanical* — every resource's variant
#   differs only in the id-argument name/help, the comment resource-type, and
#   (for ``get``) whether ``--verbose`` is offered and which default fields are
#   shown. The factory generates these directly from spec fields so the
#   per-resource boilerplate disappears.
#
# * ``list``, ``add``, and ``update`` have signatures that vary substantially
#   per resource (different filter flags, different create/update field sets,
#   resource-specific validation). Encoding these as data would be lossy and
#   risk drifting from the byte-exact CLI surface, so the spec supplies them as
#   *command-builder hooks*: plain functions carrying the exact typed Typer
#   signature. The factory registers each hook under the correct command name
#   and help string. This keeps signatures byte-identical (they are written
#   out explicitly) while still centralising app construction, command
#   registration, ``get`` comment plumbing, and ``delete``.
#
# Any of the standard operations may also be overridden wholesale via a hook
# (e.g. a resource whose ``get`` needs bespoke slimming passes ``get_hook``),
# which is how W3.3 resources with non-standard pipelines slot in without
# forking the factory.


# A command-builder hook is a fully-typed, ``@handle_errors``-decorated Typer
# command function. The factory only needs to register it; it never inspects
# the signature.
CommandHook = Callable[..., None]


@dataclass
class ResourceSpec:
    """Declarative configuration for a resource's standard command set.

    ``name`` is the CLI resource name (also the key into
    :data:`COMMENT_RESOURCE_TYPES`). ``singular``/``id_help`` shape the ``get``
    and ``delete`` id argument. ``comment_resource_type`` defaults to the
    :data:`COMMENT_RESOURCE_TYPES` entry for ``name`` when not given.

    The ``*_hook`` fields supply the resource-specific ``list``/``add``/
    ``update`` command functions; the factory registers each under its command
    name with the matching ``*_help`` string. ``get_hook`` / ``delete_hook``
    are optional wholesale overrides for resources whose get/delete pipeline is
    not the mechanical default.
    """

    name: str
    get_func_name: str
    id_arg_name: str
    id_help: str
    get_client_method: str
    list_help: str = ""
    add_help: str = ""
    update_help: str = ""
    get_help: str = "Get a single record by ID."
    delete_help: str = ""
    # ``get`` knobs (ignored when ``get_hook`` is supplied).
    get_supports_verbose: bool = False
    get_verbose_help: str = "Show all fields"
    get_default_fields: list[str] | None = None
    comment_resource_type: str | None = None
    # Per-resource command builders.
    list_hook: CommandHook | None = None
    add_hook: CommandHook | None = None
    update_hook: CommandHook | None = None
    get_hook: CommandHook | None = None
    delete_hook: CommandHook | None = None
    # Delete plumbing (ignored when ``delete_hook`` is supplied).
    delete_client_method: str = ""
    delete_label: str = ""
    # Operations to generate. Defaults to the full CRUD set sans delete.
    operations: frozenset[str] = field(
        default_factory=lambda: frozenset({"list", "get", "add", "update"})
    )


def _build_get_command(spec: ResourceSpec) -> CommandHook:
    """Generate the mechanical ``get`` command for a resource.

    Reproduces the hand-written body: fetch the record with comments merged
    (``--no-comments`` to suppress), then run the standard get-output pipeline
    (``output_get_result``) with the spec's default fields. ``--verbose`` is
    offered only when the resource opts in.
    """
    comment_type = spec.comment_resource_type or COMMENT_RESOURCE_TYPES[spec.name]
    method = spec.get_client_method
    default_fields = spec.get_default_fields

    @handle_errors
    def get_cmd_verbose(
        record_id: int = typer.Argument(..., help=spec.id_help),
        no_comments: bool = typer.Option(False, "--no-comments", help="Omit comments from output"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help=spec.get_verbose_help),
        token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
        fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
    ) -> None:
        result = run_client_with_comments(
            token, lambda c: getattr(c, method)(record_id),
            comment_type, record_id, include_comments=not no_comments,
        )
        output_get_result(result, fmt, fields=None if verbose else default_fields)

    @handle_errors
    def get_cmd_plain(
        record_id: int = typer.Argument(..., help=spec.id_help),
        no_comments: bool = typer.Option(False, "--no-comments", help="Omit comments from output"),
        token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
        fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
    ) -> None:
        result = run_client_with_comments(
            token, lambda c: getattr(c, method)(record_id),
            comment_type, record_id, include_comments=not no_comments,
        )
        output_get_result(result, fmt, fields=default_fields)

    get_cmd = get_cmd_verbose if spec.get_supports_verbose else get_cmd_plain
    return _rename_id_param(get_cmd, spec.id_arg_name, spec.get_func_name)


def _build_delete_command(spec: ResourceSpec) -> CommandHook:
    """Generate the mechanical ``delete`` command for a resource."""
    method = spec.delete_client_method
    label = spec.delete_label

    @handle_errors
    def delete_cmd(
        record_id: int = typer.Argument(..., help=spec.id_help),
        token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    ) -> None:
        run_client(token, lambda c: getattr(c, method)(record_id))
        typer.echo(f"{label} {record_id} deleted.")

    return _rename_id_param(delete_cmd, spec.id_arg_name, f"delete_{spec.name}")


def _rename_id_param(func: CommandHook, new_id_name: str, func_name: str) -> CommandHook:
    """Return a wrapper of ``func`` whose ``record_id`` parameter is renamed.

    Typer derives the id argument's display name (and the kwarg it passes back)
    from the parameter name. Generated get/delete commands use a generic
    ``record_id`` parameter; this returns a wrapper that presents it as the
    resource-specific name (``note_id``, ``project_id``) so ``wbox notes get
    --help`` shows ``NOTE_ID`` exactly as the hand-written command did, and the
    skill-ref generator sees the canonical command function name. Typer/Click
    read the rewritten ``__signature__``; the wrapper translates the kwarg back
    to ``record_id`` before delegating.
    """
    sig = inspect.signature(func)
    params = [
        p.replace(name=new_id_name) if p.name == "record_id" else p
        for p in sig.parameters.values()
    ]
    new_sig = sig.replace(parameters=params)

    def wrapper(*args: Any, **kwargs: Any) -> None:
        if new_id_name in kwargs:
            kwargs["record_id"] = kwargs.pop(new_id_name)
        func(*args, **kwargs)

    # Rebuild annotations to match the renamed signature so Typer's
    # ``get_type_hints`` pass sees the resource-specific id parameter. We do not
    # use functools.wraps: it would copy ``__wrapped__`` (pointing at the
    # original record_id signature) and confuse Typer's signature resolution.
    annotations = {p.name: p.annotation for p in params if p.annotation is not p.empty}
    if "return" in func.__annotations__:
        annotations["return"] = func.__annotations__["return"]
    wrapper.__signature__ = new_sig  # type: ignore[attr-defined]
    wrapper.__annotations__ = annotations
    wrapper.__name__ = func_name
    wrapper.__doc__ = func.__doc__
    return wrapper


def create_resource_commands(app: typer.Typer, spec: ResourceSpec) -> None:
    """Register the standard command set described by ``spec`` onto ``app``.

    Generates ``get`` and ``delete`` from the spec; registers the
    resource-supplied ``list``/``add``/``update`` hooks. Only operations listed
    in ``spec.operations`` are registered, so a resource that does not support
    delete simply omits ``"delete"`` (the API/mixin has no method to call).
    """
    if "list" in spec.operations:
        if spec.list_hook is None:
            raise ValueError(f"{spec.name}: 'list' operation requires a list_hook")
        app.command("list", help=spec.list_help)(spec.list_hook)

    if "get" in spec.operations:
        get_cmd = spec.get_hook or _build_get_command(spec)
        app.command("get", help=spec.get_help)(get_cmd)

    if "add" in spec.operations:
        if spec.add_hook is None:
            raise ValueError(f"{spec.name}: 'add' operation requires an add_hook")
        app.command("add", help=spec.add_help)(spec.add_hook)

    if "update" in spec.operations:
        if spec.update_hook is None:
            raise ValueError(f"{spec.name}: 'update' operation requires an update_hook")
        app.command("update", help=spec.update_help)(spec.update_hook)

    if "delete" in spec.operations:
        delete_cmd = spec.delete_hook or _build_delete_command(spec)
        app.command("delete", help=spec.delete_help)(delete_cmd)


__all__ = [
    "COMMENT_RESOURCE_TYPES",
    "CommandHook",
    "ResourceSpec",
    "_GetShortcutGroup",
    "create_resource_commands",
    "make_category_command",
    "make_resource_app",
]
