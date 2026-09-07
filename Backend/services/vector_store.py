import chromadb  #vector storage
from sentence_transformers import SentenceTransformer #convert text to vector embeddings


# Create local vector database
client = chromadb.PersistentClient(path="./data/chroma")

# Create collection
collection = client.get_or_create_collection(
    name="articles"
)

# Embedding model
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def store_chunks(chunks, document_url):
    embeddings = embedding_model.encode(chunks).tolist()

    ids = [
        f"{document_url}-{i}"
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[
            {"url": document_url}
            for _ in chunks
        ]
    )


def search_chunks(query, n_results=3):
    query_embedding = embedding_model.encode(
        [query]
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )

    return results