import unittest
from src.remote_api_bridge import RemoteAPIBridge
from src.config import Config

class TestRemoteAPIBridge(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.bridge = RemoteAPIBridge(self.config)

    def test_connect(self):
        self.assertFalse(self.bridge.connected)
        self.assertTrue(self.bridge.connect())
        self.assertTrue(self.bridge.connected)

    def test_disconnect(self):
        self.bridge.connect()
        self.bridge.disconnect()
        self.assertFalse(self.bridge.connected)

    def test_send_command(self):
        self.bridge.connect()
        command = {"action": "get_display"}
        response = self.bridge.send_command(command)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["command"], command)

    def test_get_display_info(self):
        self.bridge.connect()
        info = self.bridge.get_display_info()
        self.assertEqual(info["status"], "active")

    def test_unconnected_commands(self):
        with self.assertRaises(ConnectionError):
            self.bridge.send_command({"action": "test"})
        with self.assertRaises(ConnectionError):
            self.bridge.get_display_info()

if __name__ == '__main__':
    unittest.main()