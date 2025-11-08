import os
import numpy as np
from typing import List, Optional, Tuple
import google.generativeai as genai

# === Global variables ===
_faiss_index = None
_faiss_loaded = False
_genai_configured = False

FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "embeddings",
                                "faiss.index")
EMBEDDING_DIM = 768


# === Gemini Initialization ===
def configure_genai():
    """Configure Google Generative AI safely (lazy initialization)"""
    global _genai_configured
    if _genai_configured:
        return True

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ [Gemini] GEMINI_API_KEY not found in environment.")
        return False

    try:
        genai.configure(api_key=api_key)
        _genai_configured = True
        print("✅ [Gemini] API initialized successfully.")
        return True
    except Exception as e:
        print(f"❌ [Gemini] Initialization failed: {e}")
        return False


# === Embeddings ===
def get_embedding(text: str) -> Optional[List[float]]:
    """Get embedding for text using Gemini"""
    if not configure_genai():
        return None
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",  # ✅ Updated model
            content=text,
            task_type="retrieval_document")
        return result["embedding"]
    except Exception as e:
        print(f"❌ [Gemini] Error getting embedding: {e}")
        return None


def get_query_embedding(text: str) -> Optional[List[float]]:
    """Get embedding for query using Gemini"""
    if not configure_genai():
        return None
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",  # ✅ Updated model
            content=text,
            task_type="retrieval_query")
        return result["embedding"]
    except Exception as e:
        print(f"❌ [Gemini] Error getting query embedding: {e}")
        return None


# === FAISS Vector Store ===
def load_faiss_index():
    """Lazy load FAISS index"""
    global _faiss_index, _faiss_loaded
    if _faiss_loaded:
        return _faiss_index
    try:
        import faiss
        if os.path.exists(FAISS_INDEX_PATH):
            _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        else:
            _faiss_index = faiss.IndexFlatL2(EMBEDDING_DIM)
        _faiss_loaded = True
        return _faiss_index
    except Exception as e:
        print(f"❌ Error loading FAISS index: {e}")
        return None


def save_faiss_index():
    """Save FAISS index to disk"""
    global _faiss_index
    if _faiss_index is None:
        return False
    try:
        import faiss
        os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
        faiss.write_index(_faiss_index, FAISS_INDEX_PATH)
        return True
    except Exception as e:
        print(f"❌ Error saving FAISS index: {e}")
        return False


def add_embeddings(embeddings: List[List[float]]) -> bool:
    """Add embeddings to FAISS index"""
    index = load_faiss_index()
    if index is None:
        return False
    try:
        vectors = np.array(embeddings, dtype=np.float32)
        index.add(vectors)
        return save_faiss_index()
    except Exception as e:
        print(f"❌ Error adding embeddings: {e}")
        return False


def search_similar(query_embedding: List[float],
                   k: int = 3) -> Tuple[List[float], List[int]]:
    """Search for similar vectors in FAISS index"""
    index = load_faiss_index()
    if index is None or index.ntotal == 0:
        return [], []
    try:
        query_vector = np.array([query_embedding], dtype=np.float32)
        k = min(k, index.ntotal)
        distances, indices = index.search(query_vector, k)
        return distances[0].tolist(), indices[0].tolist()
    except Exception as e:
        print(f"❌ Error searching FAISS: {e}")
        return [], []


def get_embeddings_count() -> int:
    """Get count of vectors in FAISS index"""
    index = load_faiss_index()
    return index.ntotal if index else 0


def check_faiss_health() -> str:
    """Check FAISS index health"""
    if os.path.exists(FAISS_INDEX_PATH):
        try:
            index = load_faiss_index()
            return "ok" if index is not None else "error_loading"
        except:
            return "error_loading"
    return "not_ready"


# === Answer Generation ===
def generate_answer(query: str, context: str = "") -> Optional[str]:
    """Generate answer using Gemini (auto-selects best available model)"""
    if not configure_genai():
        return None

    try:
        # Prefer newer 2.5 models if available
        available_models = [m.name for m in genai.list_models()]
        preferred_models = [
            "models/gemini-2.5-flash",
            "models/gemini-2.5-pro",
            "models/gemini-flash-latest",
            "models/gemini-pro-latest",
        ]

        model_name = next(
            (m for m in preferred_models if m in available_models), None)
        if not model_name:
            print(
                f"⚠️ [Gemini] No preferred models found. Defaulting to gemini-2.5-flash."
            )
            model_name = "models/gemini-2.5-flash"

        print(f"✅ [Gemini] Using model: {model_name}")
        model = genai.GenerativeModel(model_name)

        # === Build prompt ===
        if context.strip():
            prompt = f"""You are an expert in manufacturing equipment maintenance.

Answer the user query using ONLY the provided document excerpts.
Cite document names in parentheses after claims.
If insufficient information is provided, say you don’t have enough information.

Context:
{context}

Question: {query}

Answer:"""
        else:
            prompt = f"""You are an expert in manufacturing equipment maintenance.

No documents are uploaded yet.
Provide a general answer based on best practices.
Keep your response clear, concise, and safety-focused.

Question: {query}

Answer:"""

        # === Generate response ===
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        err = str(e)
        print(f"❌ [Gemini] Error generating answer: {err}")

        if "Quota" in err or "ResourceExhausted" in err:
            return "⚠️ Gemini API quota exceeded. Wait a few hours or use a new API key."
        elif "not found" in err or "404" in err:
            return "⚠️ Gemini model not found. Please ensure your API key supports Gemini 2.5 Flash."
        elif "PERMISSION_DENIED" in err:
            return "⚠️ Your API key lacks access to Gemini models. Create a new key from Google AI Studio."
        else:
            return f"⚠️ Unexpected error: {err}"
