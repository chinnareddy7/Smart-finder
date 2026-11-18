
import os
import uuid
import secrets
import mimetypes

from functools import wraps
from flask import (
    session, request, abort, current_app,
    flash, redirect, url_for
)
from flask_login import current_user
from supabase import create_client


def allowed_file(filename):
    if not filename or '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def get_supabase_client():
    """Create and reuse the Supabase client."""

    client = current_app.extensions.get('supabase_client')

    if client is None:
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

        if not supabase_url or not supabase_key:
            raise RuntimeError(
                'SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing.'
            )

        client = create_client(supabase_url, supabase_key)
        current_app.extensions['supabase_client'] = client

    return client

class ImageUploadError(Exception):
    """Raised when an uploaded image cannot be validated or saved."""
    pass

def save_uploaded_image(file_obj):
    """
    Upload an image to Supabase Storage.
    Returns the storage path or None if upload fails.
    """

    if not file_obj or not file_obj.filename:
        return None

    if not allowed_file(file_obj.filename):
        current_app.logger.warning('Rejected invalid image format.')
        return None

    try:
        extension = file_obj.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{extension}"

        file_data = file_obj.read()

        if not file_data:
            current_app.logger.warning('Uploaded image is empty.')
            return None

        # Validate individual image size (maximum 5 MB)
        max_image_size = current_app.config['MAX_IMAGE_SIZE']

        if len(file_data) > max_image_size:
            current_app.logger.warning(
                'Image upload rejected: file exceeds 5 MB limit.'
            )
            return None

        content_type = mimetypes.guess_type(
            f"image.{extension}"
        )[0] or 'application/octet-stream'

        supabase = get_supabase_client()
        bucket_name = 'item-images'

        response = supabase.storage.from_(bucket_name).upload(
            path=unique_filename,
            file=file_data,
            file_options={
                'content-type': content_type,
                'upsert': 'false'
            }
        )

        current_app.logger.info(
            'Image successfully uploaded to Supabase: %s',
            unique_filename
        )

        return unique_filename

    except Exception:
        current_app.logger.exception(
            'Supabase image upload failed.'
        )
        return None


def get_image_url(image_filename):
    """
    Return a public Supabase URL for new images.
    Preserve support for existing absolute URLs and legacy local filenames.
    """

    if not image_filename:
        return None

    # Already a full URL
    if image_filename.startswith(('https://', 'http://')):
        return image_filename

    # New Supabase storage image
    try:
        supabase = get_supabase_client()

        response = supabase.storage.from_(
            'item-images'
        ).get_public_url(image_filename)

        if isinstance(response, str):
            return response

        if isinstance(response, dict):
            return response.get('publicUrl') or response.get('public_url')

        return getattr(response, 'public_url', None)

    except Exception:
        current_app.logger.exception(
            'Could not generate Supabase image URL.'
        )

        # Legacy images may still be stored locally.
        return url_for(
            'static',
            filename='uploads/' + image_filename
        )


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
    """Decorator ensuring that only authenticated administrators can access this endpoint."""

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not current_user.is_authenticated:
            flash(
                'Please log in with admin privileges to view this page.',
                'warning'
            )
            return redirect(
                url_for('auth.login', next=request.url)
            )

        if not getattr(current_user, 'is_admin', False):
            flash(
                'Access denied: Administrator permissions required.',
                'danger'
            )
            return redirect(url_for('student.dashboard'))

        return f(*args, **kwargs)

    return decorated_function
