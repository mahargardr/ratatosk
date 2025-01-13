import unittest
import json
from unittest.mock import mock_open, patch
from ranterstellar.global_config import GlobalConfig  # Import the GlobalConfig class from your module

class TestGlobalConfig(unittest.TestCase):
    def setUp(self):
        # Define a sample JSON configuration for testing
        self.sample_config = {
            "parameter1": "value1",
            "parameter2": "value2",
            "parameter3": 123
        }

    def test_load_config_file_not_found(self):
        # Test if FileNotFoundError is raised when the config file is not found
        with self.assertRaises(FileNotFoundError):
            config = GlobalConfig("nonexistent_config.json")

    @patch("builtins.open", new_callable=mock_open)
    def test_load_config_valid(self, mock_file):
        # Configure the mock_open to return JSON data when the file is read
        mock_file().read.return_value = json.dumps(self.sample_config)

        # Test loading a valid configuration file
        config = GlobalConfig("config.json")
        self.assertEqual(config.get_parameter("parameter1"), "value1")
        self.assertEqual(config.get_parameter("parameter2"), "value2")
        self.assertEqual(config.get_parameter("parameter3"), 123)

    @patch("builtins.open", new_callable=mock_open, read_data="invalid_json_data")
    def test_load_config_invalid_json(self, mock_file):
        # Test loading a configuration file with invalid JSON data
        with self.assertRaises(ValueError):
            config = GlobalConfig("config.json")

if __name__ == "__main__":
    unittest.main()