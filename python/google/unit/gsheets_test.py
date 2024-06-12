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
        self.assertEqual(gsheets.cell_decomp("A2"), (None, "A", 2))
        self.assertEqual(gsheets.cell_decomp("B6"), (None, "B", 6))
        self.assertEqual(gsheets.cell_decomp("C9"), (None, "C", 9))
        self.assertEqual(gsheets.cell_decomp("D"), (None, "D", -1))
        self.assertEqual(gsheets.cell_decomp("Test!D"), ("Test", "D", -1))
        self.assertEqual(gsheets.cell_decomp("'Test-1'!D"), ("Test-1", "D", -1))

    def test_range_decomp(self):
        self.assertEqual(gsheets.range_decomp("A2"), ("A2", "A2", False))
        self.assertEqual(gsheets.range_decomp("A2:A2"), ("A2", "A2", False))
        self.assertEqual(gsheets.range_decomp("A2:B6"), ("A2", "B6", True))
        self.assertEqual(gsheets.range_decomp("Sheet1!A3:B4"), ("Sheet1!A3", "B4", True))

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

    def test_expand_range(self):
        self.assertEqual(gsheets.expand_range("A3", column_width=3), "A3:D3")
        self.assertEqual(gsheets.expand_range("A3", row_height=3), "A3:A6")
        self.assertEqual(gsheets.expand_range("A3:C7", row_height=3), "A3:C10")
        self.assertEqual(gsheets.expand_range("Sheet!A4:C10", column_width=4), "Sheet!A4:G10")
        self.assertEqual(gsheets.expand_range("Sheet!A4", column_width=4), "Sheet!A4:E4")

    def test_shift_cell(self):
        self.assertEqual(gsheets.shift_cell("AB6", 5), "AG6")
        self.assertEqual(gsheets.shift_cell("Y34", 12), "AK34")
        self.assertEqual(gsheets.shift_cell("ABC23", 46, 22), "ACW45")
        self.assertEqual(gsheets.shift_cell("Test!FF12", 3, 4), "Test!FI16")
        self.assertEqual(gsheets.shift_cell("Test!g2", 2, 2), "Test!I4")

    def test_shift_range(self):
        self.assertEqual(gsheets.shift_range("AB6", 5), "AG6")
        self.assertEqual(gsheets.shift_range("Y34", 12), "AK34")
        self.assertEqual(gsheets.shift_range("ABC23", 46, 22), "ACW45")
        self.assertEqual(gsheets.shift_range("Test!FF12", 3, 4), "Test!FI16")
        self.assertEqual(gsheets.shift_range("BC2:TT3", 4, 2), "BG4:TX5")
        self.assertEqual(gsheets.shift_range("Test!F4:G7", 3, 4), "Test!I8:J11")
        self.assertEqual(gsheets.shift_range("b2:t3", 4, 2), "F4:X5")

    def test_isolate_range_by_column(self):
        self.assertEqual(gsheets.isolate_range_by_column("A5:D7", "B"), "B5:B7")
        self.assertEqual(gsheets.isolate_range_by_column("A5:A7", "B"), "B5:B7")
        self.assertEqual(gsheets.isolate_range_by_column("A5", "B"), "B5")
        self.assertEqual(gsheets.isolate_range_by_column("'Sheet-1'!A5:D7", "B"), "'Sheet-1'!B5:B7")

    def test_isolate_range_by_row(self):
        self.assertEqual(gsheets.isolate_range_by_row("A5:D7", 6), "A6:D6")
        self.assertEqual(gsheets.isolate_range_by_row("A5:A7", 6), "A6")
        self.assertEqual(gsheets.isolate_range_by_row("A5", 7), "A7")
        self.assertEqual(gsheets.isolate_range_by_row("'Sheet-1'!A5:D7", 9), "'Sheet-1'!A9:D9")

    def test_grow_range(self):
        self.assertEqual(gsheets.grow_range("A2:D10", bt=1), "A1:D11")
        self.assertEqual(gsheets.grow_range("A2:D10", bt=2), "A1:D12")
        self.assertEqual(gsheets.grow_range("D10:F20", lrbt=2), "B8:H22")
        self.assertEqual(gsheets.grow_range("B5:E10", bt=-2), "B7:E8")
        self.assertEqual(gsheets.grow_range("B5:E10", t=-2), "B7:E10")

    def test_translate_cell_info(self):
        data = [[1, 2, 3],
                ['=#[0,-1]', 2, 3]]
        self.assertEqual(gsheets.translate_cell_info("A2", data), [[1,2,3],['=A2', 2, 3]])
        data = [[1, 2, 3],
                ['=#[0,-1]+#[1,-1]+#[2,-1]']]
        self.assertEqual(gsheets.translate_cell_info("A8", data), [[1,2,3],['=A8+B8+C8']])
        data = [[1, 2, 3],
                ['=SUM(#[0,-1]:#[2,-1])']]
        self.assertEqual(gsheets.translate_cell_info("A8", data), [[1,2,3],['=SUM(A8:C8)']])
        data = [[1, 2, 3],
                ['=SUM(#[0,-1]:#[2,-1])']]
        self.assertEqual(gsheets.translate_cell_info("'Sheet-1'!A20", data), [[1,2,3],['=SUM(A20:C20)']])


    def test_get_from_range(self):
        # + / +
        self.assertEqual(gsheets.get_from_range("A5:G10", row=1), "A5")
        self.assertEqual(gsheets.get_from_range("A5:G10", row=3), "A7")
        self.assertEqual(gsheets.get_from_range("A5:G10", row=3, width=3), "A7:C7")
        self.assertEqual(gsheets.get_from_range("A5:G10", row=3, col=4, width=3), "D7:F7")
        # + / -
        self.assertEqual(gsheets.get_from_range("A5:G10", row=-1), "A10")
        self.assertEqual(gsheets.get_from_range("A5:G10", row=-1, width=2), "A10:B10")
        self.assertEqual(gsheets.get_from_range("A5:G10", col=3, row=-1), "C10")
        self.assertEqual(gsheets.get_from_range("A5:G10", col=3, row=-1, width=2), "C10:D10")
        # + / -
        self.assertEqual(gsheets.get_from_range("A5:G10", col=-1), "G5")
        self.assertEqual(gsheets.get_from_range("A5:G10", col=-1, row=3), "G7")
        self.assertEqual(gsheets.get_from_range("A5:G10", col=-2, row=3), "F7")
        self.assertEqual(gsheets.get_from_range("A5:G10", col=-2, row=3, width=2, height=3), "E7:F9")
        # - / -
        self.assertEqual(gsheets.get_from_range("A5:G10", row=-1, col=-1), "G10")
        self.assertEqual(gsheets.get_from_range("A5:G10", row=-2, col=-3), "E9")
        self.assertEqual(gsheets.get_from_range("A5:G10", row=-2, col=-3, width=2), "D9:E9")
        self.assertEqual(gsheets.get_from_range("A5:G10", row=-2, col=-3, width=2, height=4), "D6:E9")

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
