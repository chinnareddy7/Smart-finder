import os
from app import create_app
from seed_data import seed_database

if __name__ == '__main__':
    db_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'smart_lost_found.db')
    if not os.path.exists(db_file):
        print("Database not found. Initializing schema and seeding campus demo data...")
        seed_database()
        
    app = create_app()
    print("=" * 70)
    print("SMART LOST & FOUND - AI POWERED CAMPUS SYSTEM")
    print("B.Sc. Computer Science (AI & ML) Mini Project")
    print("Status: Server Running on http://127.0.0.1:5000")
    print("=" * 70)
    app.run(debug=True, host='127.0.0.1', port=5000)
