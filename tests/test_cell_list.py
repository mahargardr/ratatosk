import unittest
import pandas as pd
from unittest.mock import mock_open, patch
from ranterstellar.cell_list import CellList  # Import the GlobalConfig class from your module
from ranterstellar.exceptions import InvalidHeaderError

class TestCellList(unittest.TestCase):

    def test_load_config_file_not_found(self):
        # Test if FileNotFoundError is raised when the config file is not found
        with self.assertRaises(FileNotFoundError):
            cells = CellList("nonexistent_config.xlsx")

    def test_cell_file_invalid_header(self):
        # Test if FileNotFoundError is raised when the config file is not found
        with self.assertRaises(InvalidHeaderError):
            cells = CellList("/var/opt/so/data/cell_list/custom_cells/anchor5G.xlsx")
    
    def test_cell_file_invalid_types(self):
        # Test if FileNotFoundError is raised when the config file is not found
        with self.assertRaises(ValueError):
            cells = CellList("/var/opt/so/data/cell_list/custom_cells/anchor5G.csv")

    def test_load_cells_file_success(self):
        df = CellList("/var/opt/so/data/cell_list/custom_cells/batam-all-anchor.xlsx")
        self.assertIsInstance(df.cells_df, pd.DataFrame)

if __name__ == "__main__":
    unittest.main()