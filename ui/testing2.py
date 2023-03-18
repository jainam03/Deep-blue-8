# import csv
# import xlrd
# import codecs
# import pandas as pd
# from xlutils.filter import XLWTFormulaFilter, XLWTWriter

# fsv = "COA-L13-08-March 22.xls"
# attendee_column = 0

# if fsv.endswith('.xls'):
#     # Load the Excel file using xlrd
#     wb = xlrd.open_workbook(fsv)
#     sheet = wb.sheet_by_index(0)

#     output_workbook = XLWTWriter()
#     output_sheet = output_workbook.add_sheet(sheet.name)

#     filter = XLWTFormulaFilter()

#     unique_rows = set()

#     for row_index in range(sheet.nrows):
#         if tuple(sheet.row_values(row_index)) not in unique_rows:
#             unique_rows.add(tuple(sheet.row_values(row_index)))
#             filter.row_contents(row_index, sheet, output_sheet)

#     fsv2 = output_workbook.save('output.xls')

#     wb = xlrd.open_workbook(fsv2)
#     sheet = wb.sheet_by_index(0)
#     # Count the number of non-empty cells in the specified column
#     count = sum([1 for cell in sheet.col(attendee_column) if cell.value])-1

# elif fsv.endswith('.csv'):
#     # Read the CSV file using the csv module
#     with open(fsv, "r") as file:
#         csvReader = csv.reader(codecs.open(fsv, 'rU', 'utf-16'))
#         count = -1
#         for row in csvReader:
#             if row[attendee_column]:
#                 count += 1

# else:
#     raise ValueError("Unsupported file format")
# print("attendee count is: ", count)
