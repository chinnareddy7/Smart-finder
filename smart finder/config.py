import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'smart-lost-found-super-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'smart_lost_found.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Settings
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max size
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
