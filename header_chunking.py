from llama_index.core.node_parser import MarkdownNodeParser


def get_logical_blocks(markdown_text: str):

    # 1. Create markdown-aware parser
    parser = MarkdownNodeParser()

    # 2. Convert markdown into structured logical nodes
    nodes = parser.get_nodes_from_documents(
        documents=[markdown_text]
    )

    # 3. Return full nodes (with metadata intact)
    return nodes
