from fastapi.testclient import TestClient
from app.main import app
import pytest
import random
import string
import json
from typing import Dict, Any, Annotated

client = TestClient(app)

# Custom TestClient to handle DELETE requests with payload
class CustomTestClient(TestClient):
    """
    CustomTestClient extends the TestClient class from FastAPI's testing utilities.
    It provides additional functionality for making DELETE requests with a payload.

    Args:
        TestClient (class): The base TestClient class from FastAPI's testing utilities.

    Attributes:
        N/A

    Methods:
        delete_with_payload: Makes a DELETE request with a payload.

    Usage:
        client = CustomTestClient(app)
        response = client.delete_with_payload(url="/delete", json={"key": "value"})
    """
    def delete_with_payload(self,  **kwargs):
        return self.request(method="DELETE", **kwargs)

# Helper function to return response based on the error type
def response_helper(response: Any, query: str) -> Dict[str, Any]:
    """
    Helper function to process the response and return a formatted dictionary.

    Args:
        response (Any): The response object.
        query (Any): The query object.

    Returns:
        Dict[str, Any]: A formatted dictionary containing the response details.
    """
    response_type = response.json()['detail'][0]['type']
    response_loc = response.json()['detail'][0]['loc']
    if response_type == "int_parsing":
        return {'detail': [{'type': response_type, 'loc': response_loc, 'msg': 'Input should be a valid integer, unable to parse string as an integer', 'input': query}]}
    elif response_type == "missing":
        return {'detail': [{'type': response_type, 'loc': response_loc, 'msg': 'Field required', 'input': query}]}

# Fixture to upload a file and return the file_id
@pytest.fixture
def file_id():
    response = client.post("/upload-file/", files={"file": ("test.txt", b"file content")})
    assert response.status_code == 200
    uploaded_file = response.json()
    return uploaded_file["file_id"]

# Test the root endpoint
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

# Test the read_item endpoint
def test_read_item():
    response = client.get("/items/5")
    assert response.status_code == 200
    assert response.json() == {"item_id": 5, "q": None}

# Test the read_item endpoint with query
def test_read_item_with_query():
    response = client.get("/items/5?q=test")
    assert response.status_code == 200
    assert response.json() == {"item_id": 5, "q": "test"}

# Test the read_item endpoint with null id
def test_read_item_with_null_id():
    response = client.get("/items/null")
    assert response.status_code == 422
    assert response.json() == response_helper(response, "null")

# Test the read_item endpoint without int id
def test_read_item_without_intid():
    response = client.get("/items/abc")
    assert response.status_code == 422
    assert response.json() == response_helper(response, "abc")

# Test the update_item endpoint
def test_update_item(): 
    response = client.put("/items/5", json={"name": "test", "price": 10})
    assert response.status_code == 200
    assert response.json() == {"item_name": "test", "item_id": 5}

# Test the update_item endpoint with null id
def test_update_item_without_price():
    response = client.put("/items/5", json={"name": "test"})
    assert response.status_code == 422
    assert response.json() == response_helper(response, {"name": "test"})

# Test the update_item endpoint without name
def test_update_item_without_name():
    response = client.put("/items/5", json={"price": 10})
    assert response.status_code == 422
    assert response.json() == response_helper(response, {"price": 10})

# Test the upload_file endpoint
def test_upload_file():
    response = client.post("/upload-file/", files={"file": ("test.txt", b"file content")})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["filename"] == "test.txt"
    assert response_data["status"] == "File added to upload queue"
    # assert response_data["content_type"] == "text/plain"
    # assert response_data["file_size"] == 12
    # assert response_data["file_headers"] == {"content-disposition": 'form-data; name="file"; filename="test.txt"', "content-type": "text/plain"}
    # assert response_data["file_extension"] == "txt"
    # assert response_data["file_size_kb"] == 0.01171875


# Test get all files endpoint
def test_get_all_files():
    response = client.get("/files")
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)

# Test get file by id endpoint
def test_get_file(file_id):
    out, err = file_id.readouterr()
    print(out)
    response = client.get(f"/files/{out}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["filename"] == "test.txt"
    # assert response_data["path"] == "files/20240523-133250_test.txt"
    
# Test get file by id endpoint
def test_get_file_not_found():
    response = client.get("/files/1")
    assert response.status_code == 404
    assert response.json() == {'detail': 'File not found'}

# Test delete file by id endpoint
def test_delete_file():
    response = client.delete("/files/fe049793-2be7-4c1b-a48c-e503ddb797dc")
    assert response.status_code == 404
    # assert response.status_code == 200
    # assert response.json() == {"message": "File deleted successfully"}

# Test delete file by id endpoint
def test_delete_file_not_found():
    response = client.delete("/files/1")
    assert response.status_code == 404
    assert response.json() == {'detail': 'File not found'}

# Test multiple detele files endpoint
def test_delete_files():
    client = CustomTestClient(app)
    response = client.delete_with_payload(url="/files/", json=["fe049793-2be7-4c1b-a48c-e503ddb797dc"])
    assert response.status_code == 200 
    assert response.json() == [{"fe049793-2be7-4c1b-a48c-e503ddb797dc": "File not found"}]

# Test multiple detele files endpoint
def test_delete_files_not_found():
    client = CustomTestClient(app)
    response = client.delete_with_payload(url="/files/", json=["1","4"])
    assert response.status_code == 200
    assert response.json() == [
        {
            "1": "File not found"
        },
        {
            "4": "File not found"
        }
    ]

# =========== USER & ITEMS ===========
# Test the create_user endpoint
def test_create_user():
    email = ''.join(random.choices(string.ascii_lowercase, k=5)) + "@sahil"
    response = client.post("/users/", json={"email": email, "password": "test"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["email"] == email
    assert response_data["is_active"] == True
    assert response_data["items"] == []
    assert "id" in response_data
    assert isinstance(response_data["id"], int) 

# Test the create_user endpoint with missing email
def test_create_user_duplicate_email():
    response = client.post("/users/", json={"email": "sahil", "password": "test"})
    assert response.status_code == 400
    assert response.json() == {'detail': 'Email already registered'}

# Test the get_users endpoint
def test_get_users():
    response = client.get("/users/")
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)

# Test the read_single_user endpoint
def test_read_single_user():
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json() == {
        "email": "sahil",
        "id": 1,
        "is_active": True,
        "items": [
            {
            "title": "mac",
            "description": "m2",
            "id": 1,
            "owner_id": 1
            }
        ]
    }

# Test the read_single_user endpoint with invalid id
def test_read_single_user_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json() == {'detail': 'User not found'}

# Test the create_user_item endpoint
def test_create_user_item():
    response = client.post("/users/2/items/", json={"title": "windows", "description": "intel"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["title"] == "windows"
    assert response_data["description"] == "intel"
    assert "id" in response_data
    assert isinstance(response_data["id"], int)
    assert response_data["owner_id"] == 2

# Test the create_user_item endpoint with missing title
def test_get_items():
    response = client.get("/items/")
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)


