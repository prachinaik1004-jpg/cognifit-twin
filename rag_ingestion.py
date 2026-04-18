import os
import fitz  # This is the pymupdf library
from sentence_transformers import SentenceTransformer
from database import supabase

# Configuration
PDF_FOLDER_PATH = r"C:\Users\shriy\Desktop\backend\docs"
model = SentenceTransformer('all-MiniLM-L6-v2')

# Helper to split text manually (keeps us independent of LangChain loaders)
def chunk_text(text, chunk_size=1000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

for filename in os.listdir(PDF_FOLDER_PATH):
    if filename.endswith(".pdf"):
        print(f"Processing {filename}...")
        try:
            # 1. Open the PDF directly with fitz
            doc = fitz.open(os.path.join(PDF_FOLDER_PATH, filename))
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            
            # 2. Chunk the text
            chunks = chunk_text(full_text)
            
            # 3. Embed and Upload
            for chunk in chunks:
                if len(chunk) > 50: # Only upload meaningful chunks
                    embedding = model.encode(chunk).tolist()
                    supabase.table("memory_facts").insert({
                        "fact_text": chunk,
                        "embedding": embedding,
                        "category": "clinical"
                    }).execute()
            print(f"✅ Success: {filename}")
        except Exception as e:
            print(f"❌ Failed {filename}: {e}")