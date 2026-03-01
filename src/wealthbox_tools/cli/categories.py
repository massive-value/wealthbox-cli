from __future__ import annotations

import typer

from wealthbox_tools.models import DocumentType

from ._util import handle_errors, make_category_command, output_result, run_client

app = typer.Typer(help="Workspace-level category lookups.", no_args_is_help=True)

app.command("tags", help="List tag categories.")(make_category_command("tags"))
app.command("file-categories", help="List file category options.")(make_category_command("file_categories"))
app.command("opportunity-stages", help="List opportunity stage options.")(make_category_command("opportunity_stages"))
app.command("opportunity-pipelines", help="List opportunity pipeline options.")(make_category_command("opportunity_pipelines"))
app.command("investment-objectives", help="List investment objective options.")(make_category_command("investment_objectives"))
app.command("financial-account-types", help="List financial account type options.")(make_category_command("financial_account_types"))


@app.command("custom-fields")
@handle_errors
def custom_fields(
    document_type: DocumentType | None = typer.Option(None, "--document-type", help="Filter by document type"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """List custom field categories."""
    output_result(run_client(token, lambda c: c.list_categories("custom_fields", document_type=document_type)), fmt)
