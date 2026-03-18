from __future__ import annotations

import typer

from wealthbox_tools.models import CategoryListQuery, CategoryType, DocumentType

from ._util import OutputFormat, handle_errors, make_category_command, output_result, run_client

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, help="Workspace-level category lookups.", no_args_is_help=True)

app.command("tags", help="List tag categories.")(make_category_command(CategoryType.TAGS))
app.command("file-categories", help="List file category options.")(make_category_command(CategoryType.FILE_CATEGORIES))
app.command("opportunity-stages", help="List opportunity stage options.")(make_category_command(CategoryType.OPPORTUNITY_STAGES))
app.command("opportunity-pipelines", help="List opportunity pipeline options.")(make_category_command(CategoryType.OPPORTUNITY_PIPELINES))
app.command("investment-objectives", help="List investment objective options.")(make_category_command(CategoryType.INVESTMENT_OBJECTIVES))
app.command("financial-account-types", help="List financial account type options.")(make_category_command(CategoryType.FINANCIAL_ACCOUNT_TYPES))


@app.command("custom-fields", help="List custom field categories. Optionally filter by document type.")
@handle_errors
def custom_fields(
    document_type: DocumentType | None = typer.Option(None, "--document-type", help="Filter by document type"),
    page: int | None = typer.Option(None, help="Page number"),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    query = CategoryListQuery(document_type=document_type, page=page, per_page=per_page)
    output_result(run_client(token, lambda c: c.list_categories(CategoryType.CUSTOM_FIELDS, query)), fmt)
