import unittest
from fastapi.testclient import TestClient
from server.main import app

class TestJarvisAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'jarvis-autonomous-assistant')
        self.assertIn('gemini_configured', data)

    def test_gemini_ask_endpoint(self):
        response = self.client.post('/api/gemini/ask', json={'prompt': 'Hello JARVIS'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('answer', data)
        self.assertIn('status', data)

    def test_assistant_chat_endpoint(self):
        response = self.client.post('/api/assistant/chat', json={'prompt': 'Tell me a joke'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('answer', data)

    def test_system_stats(self):
        response = self.client.get('/api/system/stats')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'online')
        self.assertIn('cpu_usage_percent', data)
        self.assertIn('ram_usage_percent', data)

    def test_memory_endpoint(self):
        response = self.client.get('/api/assistant/memory')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_turns', data)

if __name__ == '__main__':
    unittest.main()
