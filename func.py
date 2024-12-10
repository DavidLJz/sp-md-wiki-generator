import sqlite3
from datetime import datetime
from jinja2 import Template
from typing import List
from enum import StrEnum
import msgspec
from os import environ, path
import tempfile
import subprocess

# region Dataclass
def _get_markdown_safe_text(s: str) -> str:
    s = s.strip().lower().replace(' ', '-')

    # Allow only markdown characters in hyperlink
    s = ''.join(c for c in s if c.isalnum() or c in ['-', '_'])

    return s


def get_markdown_hyperlink(text: str) -> str:
    hyperlink = _get_markdown_safe_text(text)

    return f"[{text}](#{hyperlink})"


def dict_to_struct(data: dict, struct_type: type) -> msgspec.Struct:
    return struct_type(**data)


class TextEditor(StrEnum):
    NANO = "nano"
    VIM = "vim"
    NOTEPAD = "notepad"


class Collection(msgspec.Struct, frozen=True, kw_only=True):
    id: int
    name: str
    created_at: datetime|None = None
    updated_at: datetime|None = None
    deleted_at: datetime|None = None


class Tag(msgspec.Struct, frozen=True, kw_only=True):
    id: int
    name: str
    description: str|None = None
    created_at: datetime|None = None
    updated_at: datetime|None = None
    deleted_at: datetime|None = None

    @property
    def md_link(self):
        return get_markdown_hyperlink(self.description)


class Paragraph(msgspec.Struct, frozen=True, kw_only=True):
    id: int
    title: str
    content: str

    collection: Collection|None = None
    tags: frozenset[Tag] = frozenset()

    created_at: datetime|None = None
    updated_at: datetime|None = None
    deleted_at: datetime|None = None

    @property
    def md_link(self):
        return get_markdown_hyperlink(self.title)

# endregion

# region DB functions

def get_connection():
    conn = sqlite3.connect("paragraphs.db")

    conn.row_factory = sqlite3.Row

    return conn

def initialize_database(connection: sqlite3.Connection):
    cursor = connection.cursor()

    # Create tables
    cursor.executescript("""
    -- Metadata is embedded into each table, so a separate metadata table isn't needed.
    CREATE TABLE IF NOT EXISTS collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        deleted_at DATETIME
    );

    CREATE TABLE IF NOT EXISTS paragraphs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collection_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        deleted_at DATETIME,
        FOREIGN KEY (collection_id) REFERENCES collections (id)
    );

    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        deleted_at DATETIME
    );

    CREATE TABLE IF NOT EXISTS paragraph_tags (
        paragraph_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (paragraph_id, tag_id),
        FOREIGN KEY (paragraph_id) REFERENCES paragraphs (id),
        FOREIGN KEY (tag_id) REFERENCES tags (id)
    );
    """)
    connection.commit()

# endregion

# region Paragraph

def add_paragraph(connection: sqlite3.Connection, 
                  collection_id: int, 
                  title: str, 
                  content: str, 
                  tag_ids: List[int]
                  ):
    cursor = connection.cursor()

    # Insert the paragraph
    cursor.execute("""
        INSERT INTO paragraphs (collection_id, title, content)
        VALUES (?, ?, ?)
    """, (collection_id, title, content))
    paragraph_id = cursor.lastrowid

    # Add tags to paragraph
    for tag_id in set(tag_ids):
        cursor.execute("""
            INSERT INTO paragraph_tags (paragraph_id, tag_id)
            VALUES (?, ?)
        """, (paragraph_id, tag_id))

    connection.commit()

    return paragraph_id


def update_paragraph(connection: sqlite3.Connection,
                    paragraph_id: int,
                    title: str = None,
                    content: str = None,
                    tag_ids: List[int] = None
                    ):
    cursor = connection.cursor()

    # Update the paragraph

    values = {}

    sql = "UPDATE paragraphs SET %s WHERE id = ?"   

    if title:
        values['title'] = title

    if content:
        values['content'] = content

    if not values:
        raise ValueError("No values to update")
    
    sql = sql % ', '.join(f"{key} = ?" for key in values)

    values = list(values.values())

    values.append(paragraph_id)

    cursor.execute(sql, values)

    # Update tags
    # Remove all tags
    cursor.execute("""
        DELETE FROM paragraph_tags WHERE paragraph_id = ?
    """, (paragraph_id,))

    # Add tags to paragraph
    for tag_id in set(tag_ids):
        cursor.execute("""
            INSERT INTO paragraph_tags (paragraph_id, tag_id)
            VALUES (?, ?)
        """, (paragraph_id, tag_id))

    connection.commit()


def delete_paragraph(connection: sqlite3.Connection, paragraph_id: int):
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE paragraphs
        SET deleted_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (paragraph_id,))

    connection.commit()


def get_paragraphs( connection: sqlite3.Connection,
                    paragraph_id: int = None,
                    collection_id: int = None,
                   ) -> List[Paragraph]:
    cursor = connection.cursor()

    sql = (
        'SELECT *'
        'FROM paragraphs '
        'WHERE deleted_at IS NULL'
    )

    values = []

    if paragraph_id:
        sql += ' AND id = ?'
        values.append(paragraph_id)

    if collection_id:
        sql += ' AND collection_id = ?'
        values.append(collection_id)

    rows = cursor.execute(sql, values).fetchall()

    paragraphs = []

    for row in rows:
        # Fetch collection
        collection = cursor.execute("""
            SELECT * FROM collections
            WHERE id = ?
        """, (row['collection_id'],)).fetchone()

        # Fetch tags
        tags = cursor.execute("""
            SELECT t.* FROM tags t
            JOIN paragraph_tags pt ON t.id = pt.tag_id
            WHERE pt.paragraph_id = ?
        """, (row['id'],)).fetchall()

        paragraph = Paragraph(
            id= row['id'],
            title= row['title'],
            content= row['content'],
            created_at= row['created_at'],
            updated_at= row['updated_at'],
            deleted_at= row['deleted_at'],
            collection= dict_to_struct(dict(collection), Collection) if collection else None,
            tags= frozenset(dict_to_struct(dict(tag), Tag) for tag in tags)
        )

        paragraphs.append(paragraph)

    return paragraphs

# endregion

# region Tags

def add_tag(connection: sqlite3.Connection, description: str, name: str = None):
    cursor = connection.cursor()
    
    if not name:
        name = _get_markdown_safe_text(description)
    else:
        name = _get_markdown_safe_text(name)

    if not name:
        raise ValueError("Tag name cannot be empty")

    # Insert the tag if it doesn't exist
    cursor.execute("""
        INSERT OR IGNORE INTO tags (name, description)
        VALUES (?, ?)
    """, (name, description))

    connection.commit()


def get_tags(connection: sqlite3.Connection) -> List[Tag]:
    cursor = connection.cursor()

    rows = cursor.execute("SELECT * FROM tags").fetchall()

    return [dict_to_struct(dict(row), Tag) for row in rows]


# endregion

# region Collections

def add_collection(connection: sqlite3.Connection, name: str):
    cursor = connection.cursor()

    # Insert the collection
    cursor.execute("""
        INSERT INTO collections (name)
        VALUES (?)
    """, (name,))
    connection.commit()


def get_collections(connection: sqlite3.Connection) -> List[Collection]:
    cursor = connection.cursor()

    rows = cursor.execute("SELECT * FROM collections").fetchall()

    return [dict_to_struct(dict(row), Collection) for row in rows]

# endregion

def generate_markdown(connection: sqlite3.Connection, collection_id: int):
    paragraphs = get_paragraphs(connection, collection_id= collection_id)

    tags = set(t for p in paragraphs for t in p.tags)

    # Topics Index
    markdown_template = (
        "# 1. Topics Index\n\n"
        "{% for tag in tags %}\n"
            "## {{ tag.description }}\n"
            "{% for paragraph in paragraphs if tag in paragraph.tags %}\n"
            "- {{ paragraph.md_link }}\n"
            "{% endfor %}\n"
        "{% endfor %}\n\n"
        "# 2. Excerpts\n\n"
        "{% for paragraph in paragraphs %}\n"
            "## {{ paragraph.title }}\n"
            "{{ paragraph.content }}\n\n"
            "**Tags**: {% for tag in paragraph.tags %}{{ tag.md_link }}{% if not loop.last %}, {% endif %}{% endfor %}\n"
        "{% endfor %}\n"
        )

    template = Template(markdown_template)
    
    markdown = template.render(paragraphs=paragraphs, tags=tags)

    return markdown


# region Misc

def open_content_text_editor(content: str = "", editor: TextEditor = TextEditor.NANO) -> str:
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf8', delete=False) as t:

        if content:
            t.write(content)
            t.flush()

        try:
            code = subprocess.call([editor.value, t.name])
        except FileNotFoundError:
            raise FileNotFoundError(f"Editor '{editor.value}' not found. Please ensure it is installed and in your PATH.")

        if code != 0:
            raise ValueError("Error opening text editor")
        
        t.seek(0)

        edited_content = t.read()

        return edited_content