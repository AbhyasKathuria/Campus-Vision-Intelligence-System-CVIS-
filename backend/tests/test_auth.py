import unittest
from datetime import timedelta
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.models.enums import UserRole

class TestAuthSecurity(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        raw_pw = "SecureUniversityPassword123!"
        hashed = get_password_hash(raw_pw)
        self.assertNotEqual(raw_pw, hashed)
        self.assertTrue(verify_password(raw_pw, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))

    def test_jwt_token_creation_and_decoding(self):
        payload = {"sub": "user_123", "role": UserRole.REVIEWER.value, "email": "reviewer@campus.edu"}
        token = create_access_token(payload, expires_delta=timedelta(minutes=30))
        self.assertIsInstance(token, str)

        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "user_123")
        self.assertEqual(decoded["role"], UserRole.REVIEWER.value)
        self.assertEqual(decoded["email"], "reviewer@campus.edu")

    def test_invalid_jwt_decoding(self):
        decoded = decode_access_token("completely_invalid_garbage_token")
        self.assertIsNone(decoded)

if __name__ == "__main__":
    unittest.main()
