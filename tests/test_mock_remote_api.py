import unittest
from src.mock_remote_api import MockRemoteAPI
from src.config import Config

class TestMockRemoteAPI(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.mock_api = MockRemoteAPI(self.config)

    def test_connect(self):
        self.assertFalse(self.mock_api.connected)
        self.assertTrue(self.mock_api.connect())
        self.assertTrue(self.mock_api.connected)

    def test_disconnect(self):
        self.mock_api.connect()
        self.mock_api.disconnect()
        self.assertFalse(self.mock_api.connected)

    def test_send_command(self):
        self.mock_api.connect()
        command = {"action": "get_display"}
        response = self.mock_api.send_command(command)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["command"], command)
        self.assertTrue(response["mock"])

    def test_get_display_info(self):
        self.mock_api.connect()
        info = self.mock_api.get_display_info()
        self.assertEqual(info["status"], "active")
        self.assertTrue(info["mock"])

    def test_unconnected_commands(self):
        with self.assertRaises(ConnectionError):
            self.mock_api.send_command({"action": "test"})
        with self.assertRaises(ConnectionError):
            self.mock_api.get_display_info()

if __name__ == '__main__':
    unittest.main()