import unittest
import gsheets

# Test the static methods in the module
class GSheetMethods(unittest.TestCase):
    def test_to_colour(self):
        self.assertEqual(gsheets.to_colour((0,0,0)), {'red': 0.0, 'blue': 0.0, 'green': 0.0})
        self.assertEqual(gsheets.to_colour((255,255,255)), {'red': 1.0, 'blue': 1.0, 'green': 1.0})
        self.assertEqual(gsheets.to_colour((10,10,10)), {'red': 0.0392156862745098, 'blue': 0.0392156862745098, 'green': 0.0392156862745098})

    def test_cell_addr(self):
        self.assertEqual(gsheets.cell_addr("A2"), "A2")
        self.assertEqual(gsheets.cell_addr(("B", 6)), "B6")

    def test_cell_range(self):
        self.assertEqual(gsheets.cell_range("A2"), "A2")
        self.assertEqual(gsheets.cell_range("B6", "D10"), "B6:D10")
        self.assertEqual(gsheets.cell_range("C9", "E17", "Sheet"), "Sheet!C9:E17")

    def test_cell_decomp(self):
        self.assertEqual(gsheets.cell_decomp("A2"), ("A", 2))
        self.assertEqual(gsheets.cell_decomp("B6"), ("B", 6))
        self.assertEqual(gsheets.cell_decomp("C9"), ("C", 9))
        self.assertEqual(gsheets.cell_decomp("D"), ("D", -1))

    def test_column_to_index(self):
        self.assertEqual(gsheets.column_to_index("A"), 0)
        self.assertEqual(gsheets.column_to_index("BB"), 53)
        self.assertEqual(gsheets.column_to_index("ABC"), 730)
        self.assertEqual(gsheets.column_to_index("Za"), 676)
        self.assertEqual(gsheets.column_to_index("zA"), 676)

    def test_index_to_column(self):
        self.assertEqual(gsheets.index_to_column(0), "A")
        self.assertEqual(gsheets.index_to_column(53), "BB")
        self.assertEqual(gsheets.index_to_column(730), "ABC")
        self.assertEqual(gsheets.index_to_column(676), "ZA")

    def test_shift_column(self):
        self.assertEqual(gsheets.shift_column("AB", 5), "AG")
        self.assertEqual(gsheets.shift_column("Y", 12), "AK")
        self.assertEqual(gsheets.shift_column("ABC", 46), "ACW")

    def test_cell_to_index(self):
        self.assertEqual(gsheets.cell_to_index("A2"), (0, 1))
        self.assertEqual(gsheets.cell_to_index("B6"), (1, 5))
        self.assertEqual(gsheets.cell_to_index("C9"), (2, 8))

    def test_range_to_info(self):
        self.assertEqual(gsheets.range_to_info("B5"),
                {"sheetId": 0,
                 "startColumnIndex": 1,
                 "endColumnIndex": 2,
                 "startRowIndex": 4,
                 "endRowIndex": 5})
        self.assertEqual(gsheets.range_to_info("D10"),
                {"sheetId": 0,
                 "startColumnIndex": 3,
                 "endColumnIndex": 4,
                 "startRowIndex": 9,
                 "endRowIndex": 10})
        self.assertEqual(gsheets.range_to_info("C4:G8"),
                {"sheetId": 0,
                 "startColumnIndex": 2,
                 "endColumnIndex": 7,
                 "startRowIndex": 3,
                 "endRowIndex": 8})
        self.assertEqual(gsheets.range_to_info("Test!D6:H8"),
                {"sheetId": 0,
                 "sheetName": "Test",
                 "startColumnIndex": 3,
                 "endColumnIndex": 8,
                 "startRowIndex": 5,
                 "endRowIndex": 8})

unittest.main()
