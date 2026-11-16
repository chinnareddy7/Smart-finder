import os
import uuid
import secrets
from functools import wraps
from flask import session, request, abort, current_app, flash, redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename

def allowed_file(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_image(file_obj):
    """
    Saves an uploaded image with a randomized UUID name to avoid collisions,
    and returns the saved filename or None if invalid.
    """
    if not file_obj or file_obj.filename == '':
        return None
        
    if not allowed_file(file_obj.filename):
        return None
        
    original_name = secure_filename(file_obj.filename)
    ext = original_name.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}_{int(os.times()[4])}.{ext}"
    
    upload_path = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_path, exist_ok=True)
    
    target_filepath = os.path.join(upload_path, unique_filename)
    file_obj.save(target_filepath)
    return unique_filename

def get_csrf_token():
    """Generates and stores CSRF token in the session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf(token):
    """Validates submitted CSRF token against session."""
    session_token = session.get('_csrf_token')
    if not session_token or not token:
        return False
    return secrets.compare_digest(session_token, token)

def admin_required(f):
    """Decorator ensuring that only authenticated administrators can access the endpoint."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in with admin privileges to view this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if not getattr(current_user, 'is_admin', False):
            flash('Access denied: Administrator permissions required.', 'danger')
            return redirect(url_for('student.dashboard'))
        return f(*args, **kwargs)
    return decorated_function
