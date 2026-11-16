import unittest
from datetime import date
from app import create_app
from models import db, User, LostItem, FoundItem, Match, ContactRequest
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ReportsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

        # Create two test students
        self.user1 = User(
            student_id="CS01",
            name="Alice Walker",
            email="alice@campus.edu",
            phone="1112223333",
            department="Computer Science"
        )
        self.user1.set_password("Pass123")

        self.user2 = User(
            student_id="CS02",
            name="Bob Miller",
            email="bob@campus.edu",
            phone="4445556666",
            department="Electronics"
        )
        self.user2.set_password("Pass123")

        self.admin = User(
            student_id="ADMIN01",
            name="Campus Administrator",
            email="admin@campus.edu",
            phone="9998887777",
            department="Campus Safety",
            is_admin=True
        )
        self.admin.set_password("AdminPass123")

        db.session.add_all([self.user1, self.user2, self.admin])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_report_lost_item_and_ai_trigger(self):
        # Create an existing found item first
        found = FoundItem(
            user_id=self.user2.id,
            item_name="Casio ClassWiz fx-991EX Calculator",
            category="Books & Stationery",
            description="Casio scientific calculator fx-991EX left on desk in Hall B.",
            location="Main Academic Block",
            found_date=date.today(),
            storage_location="Security Desk"
        )
        db.session.add(found)
        db.session.commit()

        # Login as user 1
        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = 'token-123'
        self.client.post('/login', data={
            'csrf_token': 'token-123',
            'identifier': 'CS01',
            'password': 'Pass123'
        })

        # Submit lost item matching the found item
        res = self.client.post('/lost/report', data={
            'csrf_token': 'token-123',
            'item_name': 'Casio fx-991EX Scientific Calculator',
            'category': 'Books & Stationery',
            'description': 'Lost my Casio fx-991EX scientific calculator during exam in Main Academic Block Hall B.',
            'location': 'Main Academic Block',
            'lost_date': date.today().strftime('%Y-%m-%d'),
            'additional_details': 'Initials AW on cover'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)

        # Check that lost item was saved
        lost = LostItem.query.filter_by(user_id=self.user1.id).first()
        self.assertIsNotNone(lost)

        # Check that AI Match was automatically generated and saved in SQLite
        match = Match.query.filter_by(lost_item_id=lost.id, found_item_id=found.id).first()
        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.similarity_score, 50.0)
        self.assertTrue(match.category_match)
        self.assertTrue(match.location_match)

    def test_contact_request_lifecycle(self):
        # Found item reported by user2
        found = FoundItem(
            user_id=self.user2.id,
            item_name="Blue Umbrella",
            category="Clothing & Accessories",
            description="Navy blue folding umbrella found in library entrance.",
            location="Central Library",
            found_date=date.today()
        )
        db.session.add(found)
        db.session.commit()

        # Login as user1 to send claim request
        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = 'token-123'
        self.client.post('/login', data={
            'csrf_token': 'token-123',
            'identifier': 'CS01',
            'password': 'Pass123'
        })

        # Send request
        req_res = self.client.post('/request/send', data={
            'csrf_token': 'token-123',
            'item_type': 'found',
            'item_id': found.id,
            'message': 'This is my blue umbrella with wooden curve handle.'
        }, follow_redirects=True)
        self.assertEqual(req_res.status_code, 200)

        contact_req = ContactRequest.query.filter_by(sender_id=self.user1.id, found_item_id=found.id).first()
        self.assertIsNotNone(contact_req)
        self.assertEqual(contact_req.status, 'Pending')

        # Logout and login as user2 to accept request
        self.client.get('/logout')
        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = 'token-123'
        self.client.post('/login', data={
            'csrf_token': 'token-123',
            'identifier': 'CS02',
            'password': 'Pass123'
        })

        accept_res = self.client.post(f'/request/{contact_req.id}/respond', data={
            'csrf_token': 'token-123',
            'action': 'accept',
            'response_note': 'Confirmed wooden handle. Call me.'
        }, follow_redirects=True)
        self.assertEqual(accept_res.status_code, 200)

        # Verify status is Accepted
        db.session.refresh(contact_req)
        self.assertEqual(contact_req.status, 'Accepted')

    def test_unauthorized_edit_prevention(self):
        # Lost item owned by user1
        lost = LostItem(
            user_id=self.user1.id,
            item_name="Personal Diary",
            category="Books & Stationery",
            description="Black leather diary.",
            location="Central Library",
            lost_date=date.today()
        )
        db.session.add(lost)
        db.session.commit()

        # Login as user2
        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = 'token-123'
        self.client.post('/login', data={
            'csrf_token': 'token-123',
            'identifier': 'CS02',
            'password': 'Pass123'
        })

        # Attempt to edit user1's item
        edit_res = self.client.get(f'/lost/{lost.id}/edit')
        self.assertEqual(edit_res.status_code, 403)


if __name__ == '__main__':
    unittest.main()
