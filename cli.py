import typer

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from func import (
    generate_markdown, 
    initialize_database, 
    get_connection,
    add_collection as db_add_collection,
    get_collections as db_get_collections,
    add_tag as db_add_tag,
    get_tags as db_get_tags,
    add_paragraph as db_add_paragraph,
    get_paragraphs as db_get_paragraphs
    )

conn = get_connection()

try:
    app = typer.Typer()

    @app.command()
    def add_collection(name: str):
        """Add a new collection."""
        db_add_collection(connection= conn, name= name)


    @app.command()
    def list_collections():
        """List all collections."""
        collections = db_get_collections(connection= conn)

        for collection in collections:
            typer.echo(f"{collection.id}. {collection.name}")
        

    @app.command()
    def add_tag(name: str, description: str = None):
        """Add a new tag."""
        db_add_tag(connection= conn, name= name, description= description)


    @app.command()
    def list_tags():
        """List all tags."""
        tags = db_get_tags(connection= conn)

        for tag in tags:
            typer.echo(f"{tag.id}. {tag.name} - {tag.description}")


    @app.command()
    def add_paragraph():
        """Add a new paragraph."""
        typer.echo("Registering a new document...")

        collections = db_get_collections(connection= conn)
        tags = db_get_tags(connection= conn)

        collections_dict = {c.name: c for c in collections}
        tags_dict = {t.name: t for t in tags}

        collection_completer = WordCompleter(collections_dict.keys(), ignore_case= True)
        tag_completer = WordCompleter(tags_dict.keys(), ignore_case= True)

        # Collection selection
        collection_name = prompt("Collection: ", completer= collection_completer)

        if not collection_name in collections_dict:
            typer.echo("Invalid collection")
            raise typer.Abort()
        
        collection_id = collections_dict[collection_name].id

        # Title
        while True:
            title = prompt("Title: ").strip()

            if title:
                break

            typer.echo("Title cannot be empty")

        # Multi-line input for document content
        typer.echo("Enter the document content. Press Ctrl+D (Unix) or Ctrl+Z (Windows) to finish:")

        content_lines = []

        try:
            while True:
                line = input()
                content_lines.append(line)
        except EOFError:
            pass

        content = "\n".join(content_lines).strip()

        if not content:
            typer.echo("Content cannot be empty")
            raise typer.Abort()

        # Interactive tag selection. Input several until an empty line is entered
        tag_list = []

        typer.echo("Enter tags from the list. Press Enter without typing anything to finish.")

        while True:
            tag_name = prompt("Tag: ", completer= tag_completer)

            if not tag_name:
                break

            tag_list.append(tag_name.strip())

        tag_ids = set()
        new_tags = set()

        for tag in tag_list:
            if tag in tags_dict:
                tag_ids.add(tags_dict[tag].id)
            else:
                continue

        db_add_paragraph(
            connection= conn,
            collection_id= collection_id,
            title= title,
            content= content,
            tag_ids= tag_ids
        )

        typer.echo("Document added successfully")


    @app.command(help= (
            "Show a paragraph. If an ID is not provided, "
            "a list of paragraphs is shown, and the user can select one to show."
            )
        )
    def show_paragraph(id: int = None):
        """Show a paragraph."""
        if id is None:
            paragraphs = db_get_paragraphs(connection= conn)

            paragraph_dict = {p.id: p for p in paragraphs}

            for paragraph in paragraphs:
                typer.echo(f"{paragraph.id}. {paragraph.title}")

            paragraph_id = typer.prompt("Enter the paragraph ID", type= int)

            if not paragraph_id or paragraph_id not in paragraph_dict:
                typer.echo("Invalid paragraph ID")
                raise typer.Abort()
            
            paragraph = paragraph_dict[ paragraph_id ]

        else:
            paragraphs = db_get_paragraphs(connection= conn, paragraph_id= id)

            if not paragraphs:
                typer.echo("Paragraph not found")
                raise typer.Abort()

            paragraph = paragraphs[0]


        typer.echo("Collection: " + paragraph.collection.name)
        typer.echo(f"ID: {paragraph.id}")
        typer.echo(f"Title: {paragraph.title}")
        typer.echo(f"Content:\n{paragraph.content}")
        typer.echo(f"Tags: {', '.join(tag.name for tag in paragraph.tags)}")

    @app.command()
    def generate(collection_id: int, output: str = None):
        """Generate Markdown file."""
        markdown = generate_markdown(connection= conn, collection_id= collection_id)

        if output:
            with open(output, 'w', encoding='utf8') as f:
                f.write(markdown)
            typer.echo(f"Markdown file saved to {output}")
        else:
            typer.echo(markdown)

    @app.command()
    def init():
        """Initialize the database."""
        initialize_database(connection= conn)


    if __name__ == "__main__":
        app()

finally:
    conn.close()
