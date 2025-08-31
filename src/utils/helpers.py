
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename: str) -> bool:
    """Verify the file extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS