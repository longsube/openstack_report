# -*- coding: utf-8 -*-

import xlsxwriter


def prepare_header(sheet, workbook):
    headers1 = ['Host', 'Ram', 'CPU']
    headers2 = ['Theory', 'Real', 'Theory']
    headers3 = ['Used (MB)', 'Total (MB)', 'Ratio (%)', 'Used (MB)', 'Total (MB)', 'Ratio (%)', 'Use (cores)', 'Total (cores)', 'Ratio (%)']
    header_format = workbook.add_format({
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'yellow'})
    sheet.merge_range('A4:K4', data='OpenStack Status', cell_format=header_format)
    sheet.merge_range('A6:A8', data=headers1[0], cell_format=header_format)
    sheet.merge_range('B6:G6', data=headers1[1], cell_format=header_format)
    sheet.merge_range('H6:K6', data=headers1[2], cell_format=header_format)
    col2 = 0
    for header2 in headers2:
        row2 = 6
        sheet.merge_range(row2, col2+1, row2, col2+3, header2,
                          cell_format=header_format)
        col2 = col2 + 3
    sheet.write(6, 10, 'Real', header_format)
    row3 = 7
    for col3, header3 in enumerate(headers3):
        col3 += 1
        sheet.write(row3, col3, header3, header_format)
    sheet.write(row3, 10, 'Percent CPU (%)', header_format)
    return sheet


def write_xls(file_name, data):
    book = xlsxwriter.Workbook(file_name)
    format_col = book.add_format({'align': 'center', 'num_format': '0.0000'})
    sheet = book.add_worksheet('OpenStack_hypervisor')
    sheet.set_column('A:A', 20, cell_format=format_col)
    sheet.set_column('B:M', 15, cell_format=format_col)
    sheet.set_default_row(20, format_col)
    sheet = prepare_header(sheet, book)
    row = 8
    for name_com, params in data.items():
        sheet.write(row, 0, name_com)
        sheet.write_number(row, 1, params.get('memory_mb_used'))
        sheet.write_number(row, 2, params.get('memory_mb'))
        if params.get('memory_mb') != 0:
            ratio_ram_theory = (float(params.get('memory_mb_used'))/float(params.get('memory_mb')))*100
           # sheet.write_formula(row, 3, '=(B{0}/C{0})*100'.format(row+1))
            sheet.write_number(row, 3, ratio_ram_theory)
        else:
            sheet.write_formula(row, 3, '0')
        sheet.write_number(row, 4, params.get('real_memory_used'))
        sheet.write_number(row, 5, params.get('real_memory_mb'))
        if params.get('real_memory_mb') != 0:
            ratio_ram_real = (float(params.get('real_memory_used')) / float(params.get('real_memory_mb'))) * 100
            sheet.write_number(row, 6, ratio_ram_real)
         #   sheet.write_formula(row, 6, '=(E{0}/F{0})*100'.format(row+1))
        else:
            sheet.write_formula(row, 6, '0')
        sheet.write_number(row, 7, params.get('vcpus_used'))
        sheet.write_number(row, 8, params.get('vcpus'))
        if params.get('vcpus') != 0:
            ratio_cpu_theory = (float(params.get('vcpus_used')) / float(params.get('vcpus'))) * 100
            sheet.write_number(row, 9, ratio_cpu_theory)
          #  sheet.write_formula(row, 9, '=(H{0}/I{0})*100'.format(row+1))
        else:
            sheet.write_formula(row, 9, '0')
        sheet.write_number(row, 10, params.get('percent_cpu'))
        row += 1
    book.close()
