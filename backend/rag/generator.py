from sentence_transformers import SentenceTransformer
from transformers import pipeline
import faiss
import numpy as np

model_embed = SentenceTransformer("all-MiniLM-L6-v2")
rag_pipeline = pipeline("text2text-generation", model="google/flan-t5-small")

def generate_questions(text, top_k=5):
    sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 30]
    embeddings = model_embed.encode(sentences, convert_to_numpy=True)

    # Create FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    # Sample queries
    queries = ["Generate a question based on the text."]
    output = []

    for query in queries:
        q_embedding = model_embed.encode([query])
        _, I = index.search(q_embedding, top_k)

        for idx in I[0]:
            context = sentences[idx]
            prompt = f"Context: {context}\nGenerate a question:"
            res = rag_pipeline(prompt, max_new_tokens=50)[0]['generated_text']
            output.append(res)

    return list(set(output))