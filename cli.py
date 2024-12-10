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
    get_paragraphs as db_get_paragraphs,
    update_paragraph as db_update_paragraph,
    delete_paragraph as db_delete_paragraph,
    open_content_text_editor,
    TextEditor
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
    def add_paragraph(text_editor: TextEditor = TextEditor.NANO, collection_id: int = None):
        """Add a new paragraph."""
        typer.echo("Registering a new document...")

        collections = db_get_collections(connection= conn)
        
        tags = db_get_tags(connection= conn)
        tags_dict = {t.name: t for t in tags}
        tag_completer = WordCompleter(tags_dict.keys(), ignore_case= True)

        if not collection_id:
            collections_dict = {c.name: c for c in collections}

            collection_completer = WordCompleter(collections_dict.keys(), ignore_case= True)

            # Collection selection
            collection_name = prompt("Collection: ", completer= collection_completer)

            if not collection_name in collections_dict:
                typer.echo("Invalid collection")
                raise typer.Abort()
            
            collection_id = collections_dict[collection_name].id

        else:
            collection = next((c for c in collections if c.id == collection_id), None)

            if not collection:
                typer.echo("Collection not found")
                raise typer.Abort()

        # Title
        while True:
            title = prompt("Title: ").strip()

            if title:
                break

            typer.echo("Title cannot be empty")

        user_instruction = (
            'You are about to modify the content of the document in a text editor.\n'
            'Please SAVE and CLOSE the editor to proceed.\n'
            'Warning: If you do not save the file, the content will not be updated and '
            'the content cannot be empty.\n'
            'Press Enter to continue.'
        )

        input(user_instruction)

        # Multi-line input for document content
        content = open_content_text_editor(content= '', editor= text_editor).strip()

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
    def modify_paragraph(id: int, text_editor: TextEditor = TextEditor.NANO):
        """Modify a paragraph."""
        paragraphs = db_get_paragraphs(connection= conn, paragraph_id= id)

        if not paragraphs:
            typer.echo("Paragraph not found")
            raise typer.Abort()

        paragraph = paragraphs[0]

        typer.echo("Leave the field empty to keep the current value.")

        title = prompt("Title: ", default= paragraph.title).strip()

        user_instruction = (
            'You are about to modify the content of the document in a text editor.\n'
            'Please SAVE and CLOSE the editor to proceed.\n'
            'Warning: If you do not save the file, the content will not be updated and '
            'the content cannot be empty.\n'
            'Press Enter to continue.'
        )

        input(user_instruction)

        content = open_content_text_editor(
            content= paragraph.content, editor= text_editor).strip()
        
        if not content:
            typer.echo("Content cannot be empty")
            raise typer.Abort()

        tags = db_get_tags(connection= conn)

        tags_dict = {tag.name: tag for tag in tags}

        tag_completer = WordCompleter(tags_dict.keys(), ignore_case= True)

        tag_list = []

        typer.echo("Enter tags from the list. Press Enter without typing anything to finish.")

        while True:
            tag_name = prompt("Tag: ", completer= tag_completer)

            if not tag_name:
                break

            if tag_name not in tags_dict:
                typer.echo("Tag not found")
                continue

            tag_list.append(tag_name.strip())

        tag_ids = set()
        new_tags = set()

        for tag in tag_list:
            if tag not in tags_dict:
                continue

            tag_ids.add(tags_dict[tag].id)

        db_update_paragraph(
            connection= conn,
            paragraph_id= paragraph.id,
            title= title,
            content= content,
            tag_ids= tag_ids
            )

        typer.echo("Document modified successfully")


    @app.command()
    def delete_paragraph(id: int):
        """Delete a paragraph."""
        paragraphs = db_get_paragraphs(connection= conn, paragraph_id= id)

        if not paragraphs:
            typer.echo("Paragraph not found")
            raise typer.Abort()

        paragraph = paragraphs[0]

        db_delete_paragraph(connection= conn, paragraph_id= paragraph.id)

        typer.echo("Document deleted successfully")


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
