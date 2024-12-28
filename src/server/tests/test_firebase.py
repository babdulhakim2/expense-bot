import pytest
from services.firebase_service import FirebaseService
import os

@pytest.fixture
def firebase_service():
    return FirebaseService()

def test_upload_media(firebase_service):
    # Test data
    user_id = "test_user"
    media_content = b"test content"
    media_type = "text/plain"
    filename = "test.txt"
    
    # Upload
    url = firebase_service.upload_media(user_id, media_content, media_type, filename)
    
    # Verify
    assert url is not None
    if os.getenv('FLASK_ENV') == 'development':
        assert 'localhost:9199' in url
    else:
        assert 'storage.googleapis.com' in url 