# Maintenance Query Agent

A full-stack AI-powered maintenance knowledge base with document ingestion, vector search, and intelligent Q&A capabilities.

## Features

- 🤖 **AI-Powered Q&A**: Uses Google Gemini for intelligent maintenance query responses
- 📚 **Document Ingestion**: Upload PDF, DOCX, and TXT maintenance manuals
- 🔍 **Vector Search**: FAISS-based semantic search for accurate document retrieval
- 🔐 **Secure Admin Panel**: Bcrypt-protected authentication with password management
- 💾 **Chat History**: SQLite-backed conversation tracking
- 🎨 **Dark Minimalist UI**: Clean, lightweight React interface
- 🛡️ **Crash Resistant**: Error boundaries and safe null-checking throughout

## Quick Start

### 1. Set up Secrets in Replit

Click on "Tools" → "Secrets" in the Replit sidebar and add:

- **GEMINI_API_KEY** (required): Get your free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **ADMIN_USER** (optional): Custom admin username (default: `yksw2403`)
- **ADMIN_PASS** (optional): Custom admin password (default: `240305`)

### 2. Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install
```

### 3. Start the Application

The application will start automatically in Replit. Alternatively, run manually:

```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 4. Run Startup Verification (Optional)

```bash
python backend/startup_check.py
```

This validates that all critical endpoints are working correctly.

## Default Admin Credentials

**Username**: `yksw2403`  
**Password**: `240305`

⚠️ **Important**: Change the default password immediately after first login via the Admin panel → Change Password section.

## Usage

### User Interface

1. **Chat Interface**: Ask maintenance-related questions in the center panel
2. **History Panel**: View and reload previous queries (left sidebar)
3. **Source Panel**: See document citations and excerpts (right sidebar)

### Admin Panel

Access at `/admin` route:

1. **Login**: Use admin credentials
2. **Upload Documents**: Add PDF, DOCX, or TXT maintenance manuals
3. **View Documents**: See list of uploaded files and processing status
4. **Change Password**: Update admin credentials securely
5. **Logout**: End admin session

### How It Works

1. **Without Documents**: Gemini provides general maintenance knowledge
2. **With Documents**: 
   - Documents are chunked and embedded using Gemini's embedding model
   - Queries are matched against document chunks using FAISS vector search
   - Top 3 relevant excerpts are used to generate accurate, cited responses

## API Endpoints

### Public Endpoints

- `GET /health` - Health check with system status
- `POST /chat` - Submit maintenance queries
- `GET /history?limit=20` - Retrieve chat history
- `GET /sources` - List uploaded documents

### Protected Endpoints (require admin token)

- `POST /admin/login` - Admin authentication
- `POST /admin/upload` - Upload maintenance documents
- `POST /admin/change-password` - Update admin password

## Architecture

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Vanilla CSS (minimal bundle size)
- **HTTP Client**: Axios
- **Routing**: React Router with lazy-loaded admin page
- **Error Handling**: Error boundaries for crash resistance

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: SQLite (metadata, history, admin)
- **Vector DB**: FAISS (lazy-loaded for performance)
- **LLM**: Google Gemini 1.5 Flash
- **Embeddings**: Gemini models/embedding-001
- **Auth**: Bcrypt + JWT sessions (in-memory)

## Project Structure

```
/frontend
  /src
    /pages
      ChatPage.jsx       # Main chat interface
      AdminPage.jsx      # Admin panel (lazy-loaded)
    /components
      ChatBox.jsx        # Message display and input
      HistoryPanel.jsx   # Query history sidebar
      SourcePanel.jsx    # Document citations
      LoginForm.jsx      # Admin authentication
      ErrorBoundary.jsx  # Error catching wrapper
    /styles
      global.css         # Dark minimalist theme
  vite.config.js
  package.json

/backend
  main.py              # FastAPI app and endpoints
  auth.py              # Authentication and JWT
  embeddings.py        # FAISS and Gemini embeddings
  db.py                # SQLite database operations
  utils.py             # File processing utilities
  startup_check.py     # Automated endpoint verification
  /data                # Uploaded document storage
  /embeddings          # FAISS index files
  db.sqlite            # SQLite database
```

## Security

- Passwords hashed with bcrypt
- JWT tokens with short expiry
- File upload sanitization and size limits (10MB)
- CORS configured for Replit preview domains
- No sensitive data in logs
- Admin sessions stored in memory only (not localStorage)

## Troubleshooting

### Frontend not loading
1. Check that Vite dev server is running on port 5173
2. Verify CORS settings in backend allow your Replit domain
3. Clear browser cache and hard refresh

### Backend errors
1. Ensure GEMINI_API_KEY is set in Replit Secrets
2. Check backend logs for specific error messages
3. Verify SQLite database was created successfully

### Login issues
1. Confirm you're using correct default credentials (yksw2403/240305)
2. Or set custom ADMIN_USER/ADMIN_PASS in Replit Secrets
3. Check backend logs for authentication errors

### Document upload fails
1. Verify file type is .pdf, .docx, or .txt
2. Check file size is under 10MB
3. Ensure GEMINI_API_KEY is valid for embeddings

## Performance

- **Lazy Loading**: FAISS and embedding modules load only when needed
- **Pagination**: History limited to 20 items per request
- **Minimal Dependencies**: No heavy UI frameworks
- **Efficient Bundling**: Vite with code-splitting for admin routes

## License

MIT License - feel free to use and modify for your maintenance operations.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review backend logs for error messages
3. Ensure all secrets are correctly configured
4. Run `python backend/startup_check.py` to verify system health
