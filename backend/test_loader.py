from pipeline.loader import load_and_extract


result = load_and_extract("your_test.pdf")

print("File:", result.file_name)
print("Pages:", result.page_count)

for page in result.pages:
    print(f"\n--- Page {page.page_num} ---")
    print(page.text[:500])