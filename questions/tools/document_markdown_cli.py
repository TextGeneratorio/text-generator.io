import click

from questions.document_processor import convert_to_markdown


@click.command()
@click.argument("source")
@click.option("-o", "--output", type=click.Path(), help="Output markdown file")
def main(source: str, output: str | None):
    """Convert DOCX/PPTX/PDF file or URL to Markdown."""
    markdown = convert_to_markdown(source)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(markdown)
    else:
        click.echo(markdown)


if __name__ == "__main__":
    main()
