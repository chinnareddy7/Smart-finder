import unittest
from app import create_app
from models import db, User
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_password_hashing(self):
        u = User(
            student_id="CS1001",
            name="Test Student",
            email="test@campus.edu",
            phone="1234567890",
            department="Computer Science"
        )
        u.set_password("MySecurePass123")
        self.assertNotEqual(u.password_hash, "MySecurePass123")
        self.assertTrue(u.check_password("MySecurePass123"))
        self.assertFalse(u.check_password("WrongPassword"))

    def test_successful_registration_and_login(self):
        # Register via client
        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = 'test-token'
            
        res = self.client.post('/register', data={
            'csrf_token': 'test-token',
            'student_id': 'CS202601',
            'name': 'Rahul Sharma',
            'email': 'rahul@campus.edu',
            'phone': '9876543210',
            'department': 'Computer Science & Engineering',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow_redirects=True)
        
        self.assertEqual(res.status_code, 200)
        user = User.query.filter_by(student_id='CS202601').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'rahul@campus.edu')

        # Logout
        self.client.get('/logout', follow_redirects=True)

        # Login with email
        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = 'test-token'
            
        login_res = self.client.post('/login', data={
            'csrf_token': 'test-token',
            'identifier': 'rahul@campus.edu',
            'password': 'Password123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Rahul', login_res.data)

    def test_duplicate_registration_prevention(self):
        # Create initial user
        u = User(
            student_id="CS202699",
            name="Existing Student",
            email="existing@campus.edu",
            phone="9876543210",
            department="IT"
        )
        u.set_password("Pass123")
        db.session.add(u)
        db.session.commit()

        # Try duplicate email
        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = 'test-token'
            
        res = self.client.post('/register', data={
            'csrf_token': 'test-token',
            'student_id': 'CS202688',
            'name': 'Another Student',
            'email': 'existing@campus.edu',
            'phone': '1111111111',
            'department': 'IT',
            'password': 'Pass123',
            'confirm_password': 'Pass123'
        }, follow_redirects=True)
        
        self.assertIn(b'already associated', res.data)

    def test_deactivated_account_login_rejection(self):
        u = User(
            student_id="CS202650",
            name="Inactive Student",
            email="inactive@campus.edu",
            phone="9876543210",
            department="IT",
            is_active=False
        )
        u.set_password("Pass123")
        db.session.add(u)
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = 'test-token'
            
        res = self.client.post('/login', data={
            'csrf_token': 'test-token',
            'identifier': 'CS202650',
            'password': 'Pass123'
        }, follow_redirects=True)
        
        self.assertIn(b'deactivated', res.data)


if __name__ == '__main__':
    unittest.main()
