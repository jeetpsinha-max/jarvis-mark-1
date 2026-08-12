import json
import pytest
from server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert data['service'] == 'jarvis-ai-assistant'
    assert 'geminiConfigured' in data
    assert 'X-RateLimit-Limit' in response.headers
    assert 'X-RateLimit-Remaining' in response.headers

def test_gemini_ask_missing_prompt(client):
    response = client.post('/api/gemini/ask', json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Bad Request'

def test_gemini_ask_valid_prompt(client):
    response = client.post('/api/gemini/ask', json={'prompt': 'Hello JARVIS'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'response' in data

def test_jarvis_command_endpoint(client):
    response = client.post('/api/jarvis/command', json={'command': 'open chrome'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['command'] == 'open chrome'
