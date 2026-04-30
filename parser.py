import os
from dotenv import load_dotenv
from llama_cloud import LlamaCloud

load_dotenv()

def parse_document(file_path:str):
    client = LlamaCloud(api_key=os.getenv("LLAMA_CLOUD_API_KEY"))

    print(f"--- Uploading {file_path} ---")
    with open(file_path, "rb") as f:
        file_obj = client.files.create(file=f, purpose="parse")

    print(f"--- Parsing {file_path} (Agentic Tier) ---")

    result = client.parsing.parse(
        file_id=file_obj.id,
        tier="agentic",
        version="latest",
        expand=["markdown"]
    )

    full_markdown = "\n\n".join([page.markdown for page in result.markdown.pages])
    
    return full_markdown

if __name__ == "__main__":
    test_file = "/Users/samadsabharwal/Documents/WORK/AI Project/AI-Copilot-for-Student-Support/data/Reinforce Club Selection Process.pdf"
    md_output = parse_document(test_file)
    
    print("\n--- PARSING COMPLETE ---")
    print(md_output)

