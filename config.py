import os

basedir = os.path.abspath(os.path.dirname(__file__))
is_vercel = os.environ.get('VERCEL') == '1'

# On Vercel, always use the hosted PostgreSQL database. SQLite files in a
# serverless deployment are temporary and cannot be used as persistent storage.
database_url = os.environ.get('DATABASE_URL', '').strip()
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)

if is_vercel and not database_url:
    raise RuntimeError('DATABASE_URL is missing. Configure Supabase PostgreSQL in Vercel Environment Variables.')
if is_vercel and database_url.startswith('sqlite:'):
    raise RuntimeError('SQLite is not supported for persistent Vercel storage. Configure Supabase PostgreSQL.')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY and is_vercel:
        raise RuntimeError('SECRET_KEY is missing. Configure it in Vercel Environment Variables.')
    SECRET_KEY = SECRET_KEY or 'local-development-only-change-me'

    default_db = os.path.join(basedir, 'smart_lost_found.db')
    SQLALCHEMY_DATABASE_URI = database_url or ('sqlite:///' + default_db)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Avoid retaining stale DB connections between short-lived serverless invocations.
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 300}
    
    # Upload Settings
        # Upload Settings
    default_uploads = '/tmp/uploads' if is_vercel else os.path.join(basedir, 'static', 'uploads')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or default_uploads
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # 6 MB total request size
    MAX_IMAGE_SIZE = 5 * 1024 * 1024      # 5 MB per image
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # AI Engine Settings
    AI_MATCH_THRESHOLD = 25.0  # Minimum percentage match to record
    AI_TOP_MATCHES_LIMIT = 5   # Max matches to surface per item
    
    # Categories & Locations for Consistent Normalization
    ITEM_CATEGORIES = [
        'Electronics',
        'Documents & ID Cards',
        'Wallets, Purses & Bags',
        'Books & Stationery',
        'Clothing & Accessories',
        'Keys & Keychains',
        'Sports Equipment',
        'Jewelry & Watches',
        'Water Bottles & Flasks',
        'Other'
    ]
    
    CAMPUS_LOCATIONS = [
        'Central Library',
        'Main Academic Block',
        'Computer Science Lab',
        'Cafeteria / Canteen',
        'Sports Complex & Ground',
        'Auditorium',
        'Science Block',
        'Engineering Workshop',
        'Student Hostels',
        'Campus Parking Area',
        'Admin Block',
        'Bus Bay & Main Gate',
        'Other / Unknown'
    ]
