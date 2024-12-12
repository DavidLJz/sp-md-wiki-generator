
# What
A single-page hyperlink-based auto-referencial self-contained knowledge base (now referred to as a **"monopedia"**) is a document that contains a **Collection** of '**Excerpts**' of information, each of which is associated with one or more '**Topics**'.

The Excerpts and Topics hyperlink to each other through a table of contents at the begginning of the document for easy navigation.

The monopedia is self-contained in that it is a single file that can contain all the content and structure of the knowledge base. Easy to share, copy, and reference without the need for additional files or dependencies.

Excerpts do not usually link to each other directly, but rather through the Topics they are associated with. This allows for a more structured and organized knowledge base, where related information is grouped together and easily navigable in a web-like manner.

This project is meant to manage the cotent, structure and generation of such a knowledge base.

# Why
I needed a way to organize my notes and thoughts in a way that is easy to navigate and reference. I wanted to be able to quickly jump between related topics and Excerpts without having to do `Ctrl+F` on a large document or having to jump between multiple files or pages.

I also wanted a way to easily share my notes with others without having to worry about formatting or compatibility issues. A single markdown file that contains all the content and structure of the knowledge base seemed like the perfect solution.

At the same time, making such a document manually would be a pain, so I decided to automate the process with a simple CLI tool.

Perhaps you have a similar need, or you just want to try out a new way of organizing your notes.

# How

## Structure
The monopedia is a markdown file that contains the following elements:

- **Collection**: A group of related Excerpts and their associated topics, resulting in a coherent body of knowledge.
- **Table of Contents**: A list of all the Excerpts in the collection, with hyperlinks to each excerpt.
- **Excerpts**: The main content of the monopedia, organized by topics and linked together by hyperlinks. (Note: For reasons, the Excerpts are referred to as 'paragraphs' in the code. Please ignore this temporary inconsistency)
- **Tags**: Keywords or phrases that represent Topics, linking related Excerpts together.

## Installation
1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage
### Initialize the Database
To initialize the database, run:
```sh
python cli.py init
```

### Add a Collection
To add a new collection, run:
```sh
python cli.py add-collection <collection-name>
```

### List Collections
To list all collections, run:
```sh
python cli.py list-collections
```

### Add a Paragraph
To add a new paragraph, run:
```sh
python cli.py add-paragraph
```
You will be prompted to enter the collection, title, content, and tags for the paragraph.

### Show a Paragraph
To show a paragraph, run:
```sh
python cli.py show-paragraph [id]
```
If an ID is not provided, a list of paragraphs will be shown, and you can select one to display.

### Modify a Paragraph
To modify a paragraph, run:
```sh
python cli.py modify-paragraph <id>
```

### Delete a Paragraph
To delete a paragraph, run:
```sh
python cli.py delete-paragraph <id>
```

### Add a Tag
To add a new tag, run:
```sh
python cli.py add-tag <description> [name]
```

### List Tags
To list all tags, run:
```sh
python cli.py list-tags
```

### Generate Markdown
To generate a Markdown file from the stored data, run:
```sh
python cli.py generate <collection-id> --output [output-file]
```
If an output file is not specified, the Markdown content will be printed to the console.

## Code Structure
- `cli.py`: Contains the CLI commands and their implementations.
- `func.py`: Contains the database functions and utility functions.
- `README.md`: This file, providing an overview of the project.

## TODO
- [ ] Change the terminology from 'paragraph' to 'excerpt'.
- [ ] Add more error handling and input validation.
- [ ] Ordering of Excerpts and Topics within a Collection.
- [ ] Support for nested Topics.
- [ ] Custom formatting and styling of the Markdown output.
- [ ] Exporting to other formats (e.g., HTML, PDF).
- [ ] Searching Excerpts by content or tags.
- [ ] Link to other Excerpts.
- [ ] Images and other media in the Excerpts.

## License
This project is licensed under the MIT License.