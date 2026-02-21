from django.http import HttpResponse
from django.conf import settings
from pathlib import Path

def serve_frontend(request, path=""):
    """Serve Quasar frontend files as static content"""
    # Map root path to index.html
    if path == "" or path == "/":
        path = "index.html"
    
    # Build file path
    file_path = settings.BASE_DIR / "frontend" / path.lstrip("/")
    
    # Security: prevent directory traversal
    if not str(file_path.resolve()).startswith(str(settings.BASE_DIR / "frontend")):
        return HttpResponse("Not Found", status=404)
    
    # Serve the file
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        # Set correct content type
        content_type = "text/html" if path.endswith(".html") else "application/octet-stream"
        return HttpResponse(content, content_type=content_type)
    except FileNotFoundError:
        # For Vue Router: return index.html for unknown routes (SPA fallback)
        if "." not in path.split("/")[-1]:
            index_path = settings.BASE_DIR / "frontend" / "index.html"
            with open(index_path, "rb") as f:
                return HttpResponse(f.read(), content_type="text/html")
        return HttpResponse("Not Found", status=404)