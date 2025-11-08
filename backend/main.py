from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime
import shutil

import db
import auth
import utils
import embeddings

app = FastAPI(title="Maintenance Query Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    query: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@app.on_event("startup")
async def startup_event():
    """Initialize database and admin user on startup"""
    db.init_database()

    admin_user = os.environ.get("ADMIN_USER", "yksw2403")
    admin_pass = os.environ.get("ADMIN_PASS", "240305")

    existing_admin = db.get_admin_user(admin_user)
    if not existing_admin:
        password_hash = auth.hash_password(admin_pass)
        created = db.create_admin_user(admin_user,
                                       password_hash,
                                       must_change=False)
        if created:
            print(f"✓ Created admin user: {admin_user}")
            if admin_user == "yksw2403":
                print(
                    f"⚠️  Using default credentials. Please change password after first login!"
                )
        else:
            print(f"ℹ️  Admin user already exists: {admin_user}")


def verify_admin_token(authorization: Optional[str] = Header(None)) -> str:
    """Verify admin authorization token"""
    if not authorization:
        raise HTTPException(status_code=401,
                            detail="Missing authorization token")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401,
                            detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = auth.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload.get("username")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_ok = db.health_check()
    faiss_status = embeddings.check_faiss_health()
    embeddings_count = embeddings.get_embeddings_count()

    return {
        "ok": db_ok and (faiss_status in ["ok", "not_ready"]),
        "db": "ok" if db_ok else "error",
        "faiss": faiss_status,
        "embeddings_count": embeddings_count,
        "checked_at": datetime.utcnow().isoformat()
    }


@app.post("/admin/login")
async def admin_login(request: LoginRequest):
    """Admin login endpoint"""
    user = db.get_admin_user(request.username)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not auth.verify_password(request.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_token(request.username)

    return {
        "token": token,
        "username": request.username,
        "must_change_password": bool(user.get('must_change_password', 0))
    }


@app.post("/admin/change-password")
async def change_password(request: ChangePasswordRequest,
                          username: str = Depends(verify_admin_token)):
    """Change admin password"""
    user = db.get_admin_user(username)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not auth.verify_password(request.current_password,
                                user['password_hash']):
        raise HTTPException(status_code=401,
                            detail="Current password is incorrect")

    valid, message = auth.validate_password_strength(request.new_password)
    if not valid:
        raise HTTPException(status_code=400, detail=message)

    new_hash = auth.hash_password(request.new_password)
    db.update_admin_password(username, new_hash)

    return {"message": "Password updated successfully"}


@app.post("/admin/upload")
async def upload_document(file: UploadFile = File(...),
                          username: str = Depends(verify_admin_token)):
    """Upload and process maintenance document"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    filename = utils.sanitize_filename(file.filename)

    if not utils.validate_file_type(filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Accepted: .pdf, .docx, .txt")

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    file_path = os.path.join(data_dir, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = utils.get_file_size_mb(file_path)
        if file_size > 10:
            os.remove(file_path)
            raise HTTPException(status_code=400,
                                detail="File too large (max 10MB)")

        text = utils.extract_text(file_path)
        chunks = utils.chunk_text(text)

        if not chunks:
            raise HTTPException(status_code=400,
                                detail="No text could be extracted from file")

        doc_id = db.add_document(filename)

        chunk_embeddings = []
        for idx, chunk in enumerate(chunks):
            embedding = embeddings.get_embedding(chunk)
            if embedding:
                chunk_embeddings.append(embedding)
                current_vector_id = embeddings.get_embeddings_count() + len(
                    chunk_embeddings) - 1
                db.add_vector_metadata(current_vector_id, doc_id, idx,
                                       chunk[:200])

        if chunk_embeddings:
            success = embeddings.add_embeddings(chunk_embeddings)
            if success:
                db.update_document_status(doc_id, "completed",
                                          len(chunk_embeddings))
                return {
                    "message": "Document processed successfully",
                    "filename": filename,
                    "chunks_processed": len(chunk_embeddings),
                    "total_chunks": len(chunks)
                }
            else:
                db.update_document_status(doc_id, "error")
                raise HTTPException(status_code=500,
                                    detail="Error adding embeddings to index")
        else:
            db.update_document_status(doc_id, "error")
            raise HTTPException(
                status_code=500,
                detail="Could not generate embeddings. Check GEMINI_API_KEY")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing upload: {e}")
        raise HTTPException(status_code=500,
                            detail=f"Error processing file: {str(e)}")


@app.post("/chat")
async def chat(request: ChatRequest):
    """Process maintenance query"""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    query = request.query.strip()

    query_embedding = embeddings.get_query_embedding(query)
    sources = []
    used_documents = False
    context = ""

    if query_embedding and embeddings.get_embeddings_count() > 0:
        distances, indices = embeddings.search_similar(query_embedding, k=3)

        if indices:
            metadata_list = db.get_vector_metadata(indices)

            for meta in metadata_list:
                sources.append({
                    "doc": meta.get('filename', 'Unknown'),
                    "excerpt": meta.get('text_snippet', '')
                })

            context_parts = []
            for meta in metadata_list:
                doc_name = meta.get('filename', 'Unknown')
                excerpt = meta.get('text_snippet', '')
                context_parts.append(f"[From {doc_name}]\n{excerpt}")

            context = "\n\n".join(context_parts)
            used_documents = True

    answer = embeddings.generate_answer(query, context)

    if not answer:
        answer = "I apologize, but I'm unable to generate a response at the moment. Please ensure the GEMINI_API_KEY is configured correctly."

    if not used_documents:
        sources = [{
            "doc":
            "General Knowledge",
            "excerpt":
            "Response based on general maintenance best practices"
        }]

    db.add_history(query, answer, sources, used_documents)

    return {
        "answer": answer,
        "sources": sources,
        "used_documents": used_documents
    }


@app.get("/history")
async def get_history(limit: int = 20):
    """Get chat history"""
    history = db.get_history(limit)
    return history


@app.delete("/history/clear")
async def clear_history():
    """Clear all chat history"""
    db.clear_history()
    return {"message": "Chat history cleared successfully"}


@app.delete("/history/{history_id}")
async def delete_history_item(history_id: int):
    """Delete a single chat history item by ID"""
    try:
        deleted = db.delete_history_item(history_id)
        if not deleted:
            raise HTTPException(status_code=404,
                                detail="History item not found")
        return {"message": f"History item {history_id} deleted successfully"}
    except Exception as e:
        print(f"Error deleting history item: {e}")
        raise HTTPException(status_code=500,
                            detail=f"Error deleting history item: {str(e)}")


@app.get("/sources")
async def get_sources():
    """Get list of uploaded documents"""
    documents = db.get_documents()
    return documents


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
