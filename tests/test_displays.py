import unittest
from src.rviz_mcp.displays.display import MockDisplay

class TestMockDisplay(unittest.TestCase):
    def setUp(self):
        self.display_data = {
            'id': 'test_display',
            'name': 'Test Display',
            'type': 'mock',
            'properties': {'color': 'red', 'size': 10}
        }
        self.display = MockDisplay(**self.display_data)

    def test_display_creation(self):
        self.assertEqual(self.display.id, 'test_display')
        self.assertEqual(self.display.name, 'Test Display')
        self.assertEqual(self.display.type, 'mock')
        self.assertEqual(self.display.properties, {'color': 'red', 'size': 10})

    def test_update_properties(self):
        self.display.update_properties({'color': 'blue', 'opacity': 0.5})
        self.assertEqual(self.display.properties, {
            'color': 'blue',
            'size': 10,
            'opacity': 0.5
        })

    def test_to_dict(self):
        display_dict = self.display.to_dict()
        self.assertEqual(display_dict, self.display_data)

if __name__ == '__main__':
    unittest.main()