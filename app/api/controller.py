from fastapi import FastAPI, HTTPException, Depends
from typing import List
from app.models import Collection, Tag, Excerpt
from app.func import (
    get_connection,
    add_collection as db_add_collection,
    get_collections as db_get_collections,
    add_tag as db_add_tag,
    get_tags as db_get_tags,
    add_paragraph as db_add_paragraph,
    get_paragraphs as db_get_paragraphs,
    update_paragraph as db_update_paragraph,
    delete_paragraph as db_delete_paragraph,
)

app = FastAPI()

# Dependency to get the database connection
def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

@app.post("/collections/", response_model=Collection)
def create_collection(collection: Collection, db = Depends(get_db)):
    db_collection = db_add_collection(db, collection.name)
    return Collection(id=db_collection.id, name=db_collection.name)

@app.get("/collections/", response_model=List[Collection])
def list_collections(db = Depends(get_db)):
    collections = db_get_collections(db)
    return [Collection(id=col.id, name=col.name) for col in collections]

@app.post("/tags/", response_model=Tag)
def create_tag(tag: Tag, db = Depends(get_db)):
    db_tag = db_add_tag(db, tag.name, tag.description)
    return Tag(id=db_tag.id, name=db_tag.name, description=db_tag.description)

@app.get("/tags/", response_model=List[Tag])
def list_tags(db = Depends(get_db)):
    tags = db_get_tags(db)
    return [Tag(id=tag.id, name=tag.name, description=tag.description) for tag in tags]

@app.post("/paragraphs/", response_model=Excerpt)
def create_paragraph(paragraph: Excerpt, db = Depends(get_db)):
    db_paragraph = db_add_paragraph(db, paragraph.title, paragraph.content, paragraph.collection_id, paragraph.tags)
    return Excerpt(id=db_paragraph.id, title=db_paragraph.title, content=db_paragraph.content, collection_id=db_paragraph.collection_id, tags=paragraph.tags)

@app.get("/paragraphs/", response_model=List[Excerpt])
def list_paragraphs(db = Depends(get_db)):
    paragraphs = db_get_paragraphs(db)
    return [Excerpt(id=para.id, title=para.title, content=para.content, collection_id=para.collection.id, tags=para.tags) for para in paragraphs]

@app.put("/paragraphs/{paragraph_id}", response_model=Excerpt)
def update_paragraph(paragraph_id: int, paragraph: Excerpt, db = Depends(get_db)):
    db_paragraph = db_update_paragraph(db, paragraph_id, paragraph.title, paragraph.content, paragraph.tags)
    if not db_paragraph:
        raise HTTPException(status_code=404, detail="Excerpt not found")
    return Excerpt(id=db_paragraph.id, title=db_paragraph.title, content=db_paragraph.content, collection_id=db_paragraph.collection_id, tags=paragraph.tags)

@app.delete("/paragraphs/{paragraph_id}")
def delete_paragraph(paragraph_id: int, db = Depends(get_db)):
    success = db_delete_paragraph(db, paragraph_id)
    if not success:
        raise HTTPException(status_code=404, detail="Excerpt not found")
    return {"detail": "Excerpt deleted successfully"}
