from datetime import date, datetime, timedelta
from app import create_app
from models import db, User, LostItem, FoundItem, Match, ContactRequest, Notification
from ai_engine.matching import recalculate_all_matches

def seed_database():
    app = create_app()
    with app.app_context():
        print("Cleaning existing tables...")
        db.drop_all()
        db.create_all()
        print("Creating campus users...")
        
        # 1. Administrator
        admin = User(
            student_id="ADMIN001",
            name="Dr. Rajesh Mehra",
            email="admin@campus.edu",
            phone="+91 98765 00001",
            department="Campus Safety & Security Office",
            is_admin=True,
            is_active=True
        )
        admin.set_password("AdminPassword123")
        db.session.add(admin)
        
        # 2. Students
        s1 = User(
            student_id="CS202401",
            name="Aarav Sharma",
            email="aarav@campus.edu",
            phone="+91 98765 11001",
            department="Computer Science & Engineering",
            is_admin=False,
            is_active=True
        )
        s1.set_password("StudentPassword123")
        
        s2 = User(
            student_id="EC202415",
            name="Priya Patel",
            email="priya@campus.edu",
            phone="+91 98765 22002",
            department="Electronics & Communication",
            is_admin=False,
            is_active=True
        )
        s2.set_password("StudentPassword123")

        s3 = User(
            student_id="ME202409",
            name="Rohan Verma",
            email="rohan@campus.edu",
            phone="+91 98765 33003",
            department="Mechanical Engineering",
            is_admin=False,
            is_active=True
        )
        s3.set_password("StudentPassword123")

        s4 = User(
            student_id="IT202422",
            name="Ananya Iyer",
            email="ananya@campus.edu",
            phone="+91 98765 44004",
            department="Information Technology",
            is_admin=False,
            is_active=True
        )
        s4.set_password("StudentPassword123")

        s5 = User(
            student_id="BT202404",
            name="Karan Malhotra",
            email="karan@campus.edu",
            phone="+91 98765 55005",
            department="Biotechnology",
            is_admin=False,
            is_active=True
        )
        s5.set_password("StudentPassword123")

        db.session.add_all([s1, s2, s3, s4, s5])
        db.session.commit()
        print("Users registered.")

        # 3. Lost Items
        today = date.today()
        
        l1 = LostItem(
            user_id=s1.id,
            item_name="Black Hydro Flask Water Bottle",
            category="Water Bottles & Flasks",
            description="I lost my matte black 750ml hydro flask water bottle in the reading hall. It has a round white NASA space mission sticker on the side.",
            location="Central Library",
            lost_date=today - timedelta(days=2),
            additional_details="Slight dent on the stainless steel bottom ring.",
            status="Lost"
        )

        l2 = LostItem(
            user_id=s2.id,
            item_name="Casio fx-991EX ClassWiz Scientific Calculator",
            category="Books & Stationery",
            description="Black and white Casio fx-991EX engineering scientific calculator left on row 3 bench during morning math exam.",
            location="Main Academic Block",
            lost_date=today - timedelta(days=3),
            additional_details="Has initials 'P.P.' engraved lightly inside the protective sliding cover.",
            status="Lost"
        )

        l3 = LostItem(
            user_id=s3.id,
            item_name="Brown Leather Fossil Bifold Wallet",
            category="Wallets, Purses & Bags",
            description="Brown genuine leather bifold wallet forgotten on lunch table. Contains college student ID card and city metro transit card.",
            location="Cafeteria / Canteen",
            lost_date=today - timedelta(days=1),
            additional_details="Contains Rohan Verma's student card ending in 2409.",
            status="Lost"
        )

        l4 = LostItem(
            user_id=s4.id,
            item_name="Sony WH-1000XM4 Wireless Noise-Cancelling Headphones",
            category="Electronics",
            description="Silver grey Sony over-ear wireless headphones kept in their original black zippered carrying case with audio cable.",
            location="Central Library",
            lost_date=today - timedelta(days=4),
            additional_details="Custom small orange cable tie on the zipper pull.",
            status="Lost"
        )

        l5 = LostItem(
            user_id=s5.id,
            item_name="Honda Car Remote Key with Blue Keychain",
            category="Keys & Keychains",
            description="Honda 3-button car remote key attached to an anodized blue aluminum carabiner keychain.",
            location="Campus Parking Area",
            lost_date=today - timedelta(days=1),
            additional_details="Key has a small rubber scratch guard on the lock button.",
            status="Lost"
        )

        l6 = LostItem(
            user_id=s1.id,
            item_name="Blue Logitech Wireless Optical Mouse",
            category="Electronics",
            description="Logitech M235 wireless optical mouse blue and black finish, lost in coding lab.",
            location="Computer Science Lab",
            lost_date=today - timedelta(days=5),
            additional_details="Nano USB receiver was left plugged in or lost alongside it.",
            status="Recovered"
        )

        db.session.add_all([l1, l2, l3, l4, l5, l6])
        db.session.commit()
        print("Lost items registered.")

        # 4. Found Items
        f1 = FoundItem(
            user_id=s4.id,
            item_name="Black Metal Water Bottle with NASA Space Sticker",
            category="Water Bottles & Flasks",
            description="Black insulated metal water flask found sitting on a study desk near Central Library bookshelf. Has a prominent NASA sticker.",
            location="Central Library",
            found_date=today - timedelta(days=1),
            storage_location="Central Library Security Desk / Issue Counter",
            additional_details="Flask is clean and currently safely kept with the chief librarian.",
            status="Found"
        )

        f2 = FoundItem(
            user_id=s3.id,
            item_name="Casio ClassWiz fx-991EX Calculator",
            category="Books & Stationery",
            description="Found a scientific calculator Casio fx-991EX model in Lecture Hall B after the mathematics examination.",
            location="Main Academic Block",
            found_date=today - timedelta(days=2),
            storage_location="Main Academic Block Faculty Staffroom A-12",
            additional_details="Sliding cover is intact with faint handwriting on interior.",
            status="Found"
        )

        f3 = FoundItem(
            user_id=s2.id,
            item_name="Men's Brown Leather Wallet",
            category="Wallets, Purses & Bags",
            description="Brown leather wallet found on cafeteria table near juice counter. Student cards safely held inside.",
            location="Cafeteria / Canteen",
            found_date=today - timedelta(days=1),
            storage_location="Dean Student Welfare Office, 1st Floor Admin Block",
            additional_details="Owner can verify identity card number to collect.",
            status="Found"
        )

        f4 = FoundItem(
            user_id=s1.id,
            item_name="Honda Vehicle Smart Key with Blue Ring",
            category="Keys & Keychains",
            description="Found car key for Honda vehicle with blue carabiner keychain on the pavement near the two-wheeler parking lot.",
            location="Campus Parking Area",
            found_date=today - timedelta(days=1),
            storage_location="Main Gate Security Guard Cabin",
            additional_details="Handed over directly to head guard on duty.",
            status="Found"
        )

        f5 = FoundItem(
            user_id=s5.id,
            item_name="Logitech Compact Wireless Mouse",
            category="Electronics",
            description="Dark blue and black Logitech wireless mouse left next to desktop system number 28 in lab.",
            location="Computer Science Lab",
            found_date=today - timedelta(days=4),
            storage_location="Returned to Aarav Sharma",
            additional_details="Already claimed and handed over to owner.",
            status="Claimed"
        )

        db.session.add_all([f1, f2, f3, f4, f5])
        db.session.commit()
        print("Found items registered.")

        # 5. Execute AI Engine calculation across items
        print("Calculating real AI TF-IDF Cosine Similarity & Hybrid Matches...")
        computed_count = recalculate_all_matches(db, threshold=25.0)
        print(f"Generated {computed_count} AI comparison records in SQLite!")

        # 6. Sample Contact Request & Notifications
        req1 = ContactRequest(
            sender_id=s3.id,  # Rohan
            receiver_id=s2.id, # Priya who found the wallet
            item_type="found",
            found_item_id=f3.id,
            message="Hi Priya, I believe that is my brown Fossil wallet lost yesterday in the cafeteria. My student ID (CS/ME) and name Rohan are inside. Could we coordinate handover?",
            status="Accepted",
            response_note="Verified! The ID matches your name. Please collect it from the Dean Office or message me on WhatsApp."
        )
        db.session.add(req1)

        # Notifications
        n1 = Notification(
            user_id=s1.id,
            title="High Confidence AI Match (92%)!",
            message="Our AI identified a 92% match between your lost 'Black Hydro Flask' and a found item at Central Library.",
            notification_type="match_found",
            link="/matches",
            is_read=False
        )
        n2 = Notification(
            user_id=s2.id,
            title="High Confidence AI Match (88%)!",
            message="Our AI detected a strong match for your lost Casio Scientific Calculator in Main Academic Block.",
            notification_type="match_found",
            link="/matches",
            is_read=False
        )
        n3 = Notification(
            user_id=s3.id,
            title="Claim Request Accepted!",
            message="Priya Patel accepted your claim request for 'Men's Brown Leather Wallet'. Contact information is now unlocked.",
            notification_type="request_accepted",
            link="/my-reports?tab=outgoing",
            is_read=False
        )
        db.session.add_all([n1, n2, n3])
        db.session.commit()
        print("Demo seed complete! Database is primed and ready.")

if __name__ == '__main__':
    seed_database()
