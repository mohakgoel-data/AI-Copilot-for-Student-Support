import os
from dotenv import load_dotenv
from llama_cloud import LlamaCloud

from llama_index_pipeline import process_markdown

load_dotenv()


def parse_document(file_path: str):
    client = LlamaCloud(api_key=os.getenv("LLAMA_CLOUD_API_KEY"))

    with open(file_path, "rb") as f:
        file_obj = client.files.create(file=f, purpose="parse")

    result = client.parsing.parse(
        file_id=file_obj.id,
        tier="agentic",
        version="latest",
        expand=["markdown"]
    )

    full_markdown = "\n\n".join(
        [page.markdown for page in result.markdown.pages]
    )

    return full_markdown


# FINAL PIPELINE (ENTRY POINT)
def run_pipeline(file_path: str):

    # Step 1: Parse
    markdown = parse_document(file_path)

    # Step 2: LlamaIndex processing
    blocks = process_markdown(markdown, file_path)

    return blocks


