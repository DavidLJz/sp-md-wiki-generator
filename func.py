import sqlite3
from datetime import datetime
from jinja2 import Template
from typing import List
import msgspec

# region Dataclass

def dict_to_struct(data: dict, struct_type: type) -> msgspec.Struct:
    return struct_type(**data)


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

# endregion

# region Tags

def add_tag(connection: sqlite3.Connection, name: str, description: str = None):
    cursor = connection.cursor()
    
    description = description.strip() if description else name

    name = name.strip().lower().replace(' ', '-')

    if not name:
        raise ValueError("Tag name cannot be empty")

    # Insert the tag
    cursor.execute("""
        INSERT INTO tags (name, description)
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

def generate_markdown(connection: sqlite3.Connection, collection_id: int = None):
    cursor = connection.cursor()

    # Fetch all data
    collections = cursor.execute("SELECT * FROM collections").fetchall()
    paragraphs = cursor.execute("""
        SELECT p.id, p.title, p.content, c.name AS collection_name, 
               GROUP_CONCAT(t.name, ', ') AS tags
        FROM paragraphs p
        LEFT JOIN collections c ON p.collection_id = c.id
        LEFT JOIN paragraph_tags pt ON p.id = pt.paragraph_id
        LEFT JOIN tags t ON t.id = pt.tag_id
        WHERE p.deleted_at IS NULL
        GROUP BY p.id
    """).fetchall()

    # Template
    markdown_template = """
    # Paragraphs Collection

    {% for collection in collections %}
    ## {{ collection['name'] }}

    {% for paragraph in paragraphs if paragraph['collection_name'] == collection['name'] %}
    ### {{ paragraph['title'] }}
    {{ paragraph['content'] }}

    **Tags:** {{ paragraph['tags'] }}

    ---
    {% endfor %}
    {% endfor %}
    """
    template = Template(markdown_template)
    markdown = template.render(collections=collections, paragraphs=paragraphs)

    # Write to file
    with open("output.md", "w") as f:
        f.write(markdown)
