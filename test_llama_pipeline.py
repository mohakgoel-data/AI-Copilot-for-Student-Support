from ingestion_pipeline.llama_index_pipeline import process_markdown


MARKDOWN_FILE = "./data/output.md"


with open(MARKDOWN_FILE, "r", encoding="utf-8") as file:
    markdown_text = file.read()


logical_blocks = process_markdown(
    markdown_text=markdown_text,
    file_path=MARKDOWN_FILE
)


print("\n" + "=" * 70)
print("TOTAL LOGICAL BLOCKS:", len(logical_blocks))
print("=" * 70)


for index, block in enumerate(logical_blocks, start=1):

    print(f"\nLOGICAL BLOCK {index}")
    print("-" * 70)

    print("CONTENT:")
    print(block["content"])

    print("\nMETADATA:")
    print(block["metadata"])

    print("-" * 70)