import unittest
from src.rviz_mcp.displays.display_manager import DisplayManager

class TestDisplayManager(unittest.TestCase):
    def setUp(self):
        self.manager = DisplayManager()
        self.display_data = {
            'id': 'test_display',
            'name': 'Test Display',
            'type': 'mock',
            'properties': {'color': 'red', 'size': 10}
        }

    def test_create_display(self):
        display = self.manager.create_display(self.display_data)
        self.assertEqual(display.id, 'test_display')
        self.assertEqual(len(self.manager.get_all_displays()), 1)

    def test_get_display(self):
        self.manager.create_display(self.display_data)
        display = self.manager.get_display('test_display')
        self.assertIsNotNone(display)
        self.assertEqual(display.name, 'Test Display')

    def test_update_display(self):
        self.manager.create_display(self.display_data)
        updated_display = self.manager.update_display('test_display', {'color': 'blue'})
        self.assertEqual(updated_display.properties['color'], 'blue')

    def test_delete_display(self):
        self.manager.create_display(self.display_data)
        result = self.manager.delete_display('test_display')
        self.assertTrue(result)
        self.assertEqual(len(self.manager.get_all_displays()), 0)

if __name__ == '__main__':
    unittest.main()