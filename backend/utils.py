import os
import re
from typing import List, Tuple
from pathlib import Path

def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename"""
    name = os.path.basename(filename)
    name = re.sub(r'[^\w\s.-]', '', name)
    name = name[:200]
    return name

def validate_file_type(filename: str) -> bool:
    """Validate file extension"""
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    ext = Path(filename).suffix.lower()
    return ext in allowed_extensions

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from .txt file"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from .docx file"""
    from docx import Document
    doc = Document(file_path)
    text = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text.append(paragraph.text)
    return '\n'.join(text)

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from .pdf file"""
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
    return '\n'.join(text)

def extract_text(file_path: str) -> str:
    """Extract text from supported file types"""
    ext = Path(file_path).suffix.lower()
    
    if ext == '.txt':
        return extract_text_from_txt(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.pdf':
        return extract_text_from_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk.strip():
            chunks.append(chunk.strip())
        
        start += (chunk_size - overlap)
    
    return chunks

def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB"""
    return os.path.getsize(file_path) / (1024 * 1024)
