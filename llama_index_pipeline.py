import os
import re
from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser




def get_nodes_from_markdown(markdown_text: str):
    
    parser = MarkdownNodeParser()

    document = Document(text=markdown_text)

    nodes = parser.get_nodes_from_documents([document])

    return nodes




def clean_header(header: str):
    if not header:
        return "Root"

    return re.sub(r'^\d+(\.\d+)*\s*', '', header).strip()
     

def build_hierarchy(parts):
    return " > ".join(parts) if parts else "Root"


def attach_metadata(nodes, filename: str):

    for node in nodes:

        raw_path = node.metadata.get("header_path", "/")
        parts = [p for p in raw_path.split("/") if p]

        cleaned = [clean_header(p) for p in parts]

        node.metadata = {
            "source_name": os.path.basename(filename),
            "hierarchy": build_hierarchy(cleaned)
        }

    return nodes



def create_logical_blocks(nodes):

    logical_blocks = []

    for node in nodes:

        block = {
            "content": node.text.strip(),
            "metadata": {
                "source_name": node.metadata.get("source_name"),
                "hierarchy": node.metadata.get("hierarchy")
            }
        }

        logical_blocks.append(block)

    return logical_blocks




def process_markdown(markdown_text: str, file_path: str):


    nodes = get_nodes_from_markdown(markdown_text)

    nodes = attach_metadata(nodes, file_path)

    logical_blocks = create_logical_blocks(nodes)

    return logical_blocks