# -*- coding: utf-8 -*-

import xlsxwriter


def prepare_header(sheet, workbook):
    headers1 = ['Pool', 'Storage']
    headers2 = ['Theory', 'Real']
    headers3 = ['Used (GB)', 'Total (GB)', 'Ratio (%)']*2
    header_format = workbook.add_format({
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'yellow'})
    sheet.merge_range('A4:G4', data='Ceph Status', cell_format=header_format)
    sheet.merge_range('A6:A8', data=headers1[0], cell_format=header_format)
    sheet.merge_range('B6:G6', data=headers1[1], cell_format=header_format)
    col2 = 0
    for header2 in headers2:
        row2 = 6
        sheet.merge_range(row2, col2+1, row2, col2+3, header2,
                          cell_format=header_format)
        col2 = col2 + 3
    row3 = 7
    for col3, header3 in enumerate(headers3):
        col3 += 1
        sheet.write(row3, col3, header3, header_format)
    return sheet


def write_xls(file_name, data):
    book = xlsxwriter.Workbook(file_name)
    format_col = book.add_format({'align': 'center', 'num_format': '0.0000'})
    sheet = book.add_worksheet('Storage_Usage')
    sheet.set_column('A:A', 20, cell_format=format_col)
    sheet.set_column('B:M', 15, cell_format=format_col)
    sheet.set_default_row(20, format_col)
    sheet = prepare_header(sheet, book)
    row = 8
    for name_com, params in data.items():
        sheet.write(row, 0, name_com)
        sheet.write_number(row, 1, params.get('used_gb'))
        sheet.write_number(row, 2, params.get('total_gb'))
        if params.get('total_gb') != 0:
            ratio_storage_theory = (float(params.get('used_gb')) / float(params.get('total_gb'))) * 100
            sheet.write_number(row, 3, ratio_storage_theory)
       #     sheet.write_formula(row, 3, '=(B{0}/C{0})*100'.format(row+1))
        else:
            sheet.write_formula(row, 3, '0')
        sheet.write_number(row, 4, params.get('real_used_gb'))
        sheet.write_number(row, 5, params.get('real_total_gb'))
        if params.get('real_total_gb') != 0:
            ratio_storage_real = (float(params.get('real_used_gb')) / float(params.get('real_total_gb'))) * 100
            sheet.write_number(row, 6, ratio_storage_real)
           # sheet.write_formula(row, 6, '=(E{0}/F{0})*100'.format(row+1))
        else:
            sheet.write_formula(row, 6, '0')
        row += 1
    book.close()
