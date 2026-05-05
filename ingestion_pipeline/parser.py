import os
from dotenv import load_dotenv
from llama_cloud import LlamaCloud

load_dotenv()


def parse_document(file):

    client = LlamaCloud(api_key=os.getenv("LLAMA_CLOUD_API_KEY"))

    file.seek(0)

    file_obj = client.files.create(
        file=file,
        purpose="parse"
    )

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

