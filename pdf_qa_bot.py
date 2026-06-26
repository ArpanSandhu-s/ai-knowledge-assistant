from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM

# =========================
# STEP 1: Load PDF
# =========================

loader = PyPDFLoader("Arpan_Sandhu_Resume_2026.pdf")
pages = loader.load()

print(f"\nPages loaded: {len(pages)}")

# =========================
# STEP 2: Chunk PDF
# =========================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

docs = splitter.split_documents(pages)

print(f"Chunks created: {len(docs)}")

print("\nFirst 3 Chunks Preview:\n")

for i, doc in enumerate(docs[:3]):
    print(f"Chunk {i+1}")
    print("-" * 50)
    print(doc.page_content[:300])
    print()

# =========================
# STEP 3: Create Embeddings
# =========================

print("\nCreating embeddings...")

embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)

# =========================
# STEP 4: Create FAISS DB
# =========================

vectorstore = FAISS.from_documents(
    docs,
    embeddings
)

print("Vector database created successfully!")

# =========================
# STEP 5: Load LLM
# =========================

llm = OllamaLLM(
    model="llama3.2",
    temperature=0
)

# =========================
# STEP 6: Ask Questions
# =========================

questions = [
    "What is Arpan's CGPA?",
    "Where is Arpan currently working?",
    "What technical skills does Arpan have?"
]

for query in questions:

    print("\n" + "=" * 80)
    print(f"QUESTION: {query}")
    print("=" * 80)

    # Retrieve relevant chunks
    results = vectorstore.similarity_search(
        query,
        k=3
    )

    print("\nRetrieved Chunks:\n")

    for i, doc in enumerate(results):
        print(f"\nResult {i+1}")
        print("-" * 50)
        print(doc.page_content)

    # Build context
    context = "\n\n".join(
        [doc.page_content for doc in results]
    )

    # Prompt
    prompt = f"""
Answer the question using ONLY the context below.

If the answer is not present in the context, say:
"I don't know."

Context:
{context}

Question:
{query}

Answer:
"""

    # Get answer
    answer = llm.invoke(prompt)

    print("\nFinal Answer:")
    print("-" * 50)
    print(answer)

print("\n\nRAG Pipeline Completed Successfully!")






# live chat in place of questions:::
while True:
    query = input("\nAsk a question (or type quit): ")

    if query.lower() == "quit":
        break

    results = vectorstore.similarity_search(query, k=3)

    # build context
    # call llm
    # print answer