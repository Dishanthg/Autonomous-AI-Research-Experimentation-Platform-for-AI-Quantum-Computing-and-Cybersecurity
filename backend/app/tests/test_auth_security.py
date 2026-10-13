import jwt
import pytest

from app.security.auth import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_is_not_plaintext():
    hashed = hash_password("supersecret123")
    assert hashed != "supersecret123"
    assert verify_password("supersecret123", hashed)


def test_password_verify_rejects_wrong_password():
    hashed = hash_password("supersecret123")
    assert not verify_password("wrongpassword", hashed)


def test_access_token_roundtrip():
    token = create_access_token(subject="user-123", role="RESEARCHER")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "RESEARCHER"


def test_access_token_rejects_tampering():
    token = create_access_token(subject="user-123", role="RESEARCHER")
    tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)
