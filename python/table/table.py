def format(headers, matrix,
           top_format='{:^{}}',
           left_format='{:<{}}',
           cell_format='{:>{}}',
           row_delim='\n',
           col_delim=' | '):

    table = [headers] + [row for row in matrix]
    table_format = [['{:^{}}'] + len(headers) * [top_format]] \
        + len(matrix) * [[left_format] + len(headers) * [cell_format]]
    col_widths = [max(len(format.format(cell, 0))
                      for format, cell in zip(col_format, col))
                  for col_format, col in zip(zip(*table_format), zip(*table))]
    return row_delim.join(
                col_delim.join(
                    format.format(cell, width)
                    for format, cell, width in
                    zip(row_format, row, col_widths))
                for row_format, row in zip(table_format, table))
