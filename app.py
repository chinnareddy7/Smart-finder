import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, session, abort, send_from_directory
from flask_login import LoginManager
from config import Config
from models import db, User
from utils import get_csrf_token

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Serve favicon.ico safely without crashing on missing files
    @app.route('/favicon.ico')
    def favicon():
        favicon_path = os.path.join(app.root_path, 'static', 'favicon.ico')
        if os.path.exists(favicon_path):
            return send_from_directory(
                os.path.join(app.root_path, 'static'),
                'favicon.ico',
                mimetype='image/x-icon'
            )
        return ('', 204)

    # Initialize extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.lost import lost_bp
    from routes.found import found_bp
    from routes.matches import matches_bp
    from routes.requests import requests_bp
    from routes.admin import admin_bp
    from routes.notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(lost_bp)
    app.register_blueprint(found_bp)
    app.register_blueprint(matches_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)

    # Context processors
    @app.context_processor
    def inject_global_template_vars():
        return {
            'csrf_token': get_csrf_token(),
            'ITEM_CATEGORIES': app.config['ITEM_CATEGORIES'],
            'CAMPUS_LOCATIONS': app.config['CAMPUS_LOCATIONS'],
            'current_year': datetime.now().year
        }

    # Custom Jinja filters
    @app.template_filter('format_date')
    def format_date(value, format_str='%b %d, %Y'):
        if not value:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
        return value.strftime(format_str)

    @app.template_filter('time_ago')
    def time_ago(dt):
        if not dt:
            return ''
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        diff = now - dt
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours}h ago"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days}d ago"
        else:
            return dt.strftime('%b %d, %Y')

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_title="404 - Page Not Found", 
                               error_msg="The page you are looking for does not exist or has been moved."), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('base.html', error_title="403 - Forbidden Access", 
                               error_msg="You do not have permission to view this resource."), 403

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('base.html', error_title="413 - File Too Large", 
                               error_msg="The uploaded file exceeds the 5MB file size limit."), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', error_title="500 - Server Error", 
                               error_msg="An unexpected error occurred. Please try again later."), 500

    # Ensure upload directory exists safely
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except Exception:
        pass

    with app.app_context():
        try:
            db.create_all()
        except Exception:
            pass

    return app

# Expose app and application at module level for Vercel/WSGI serverless deployment
app = create_app()
application = app

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
