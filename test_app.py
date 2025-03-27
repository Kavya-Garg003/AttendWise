import unittest
from app import app

class FlaskTestCase(unittest.TestCase):

    # Test if the home page loads
    def test_home(self):
        tester = app.test_client(self)
        response = tester.get('/')
        self.assertEqual(response.status_code, 200)

    # Test login page loads
    def test_login_page(self):
        tester = app.test_client(self)
        response = tester.get('/login')
        self.assertEqual(response.status_code, 200)

    # Test if registration works
    def test_register(self):
        tester = app.test_client(self)
        response = tester.post('/register', data=dict(
            student_id="test123",
            name="Test User",
            email="testuser@example.com",
            age="20",
            gender="Male",
            phone="9876543210",
            password="password123"
        ), follow_redirects=True)
        self.assertIn(b'Registration successful!', response.data)

if __name__ == '__main__':
    unittest.main()
