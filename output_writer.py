import fpdf
from fpdf import FPDF


def get_school_year(month_num: int, year: int) -> tuple:
    '''
    Returns the corresponding school year (e.g. 2022-2023)
    :param month_num: report's month number (from 1 to 12)
    :param year:  report's year
    :return: (int, int) - school year
    '''
    if month_num <= 7:
        return year - 1, year
    else:
        return year, year + 1


def create_table(rev: float, labour_expenses: float, labour_tax_free: float,
                 teacher_salary: float, admin_salaries: dict, labour_tax: float, indirect_costs: float,
                 lab_exp_ratio: float, teach_sal_ratio: float, indir_cost_ratio: float) -> tuple:
    '''
        Creates the gist of the report: the "table" with data, without the headers and the signature
        :param rev: revenue (entered by the user)
        :param labour_expenses: total expenses on labour (calculated within the program)
        :param labour_tax_free: tax-free expenses on labour (calculated within the program)
        :param teacher_salary: teacher's salary (calculated within the program)
        :param admin_salaries: dictionary of admin_salaries (calculated within the program)
        :param labour_tax: expenses on social security (calculated within the program)
        :param indirect_costs: indirect costs (calculated within the program)
        :param lab_exp_ratio: labour/total expense ratio (calculated within the program)
        :param teach_sal_ratio: teacher salary/labour expenses ratio (calculated within the program)
        :param indir_cost_ratio: indirect costs/total expenses ratio (calculated within the program)
        :return res: tuple[tuples] - "table": tuple of rows, each of 4 elements
        '''
    empty_row = ('', '', '', '')
    res = (
        ('**№ п/п**', '**Основные статьи**', '**сумма**', '**примечание**'),
        empty_row,
        (1, '**Доходы**', rev, ''),
        empty_row,
        (2, '**Расходы (ЗП с ЕСН)**', labour_expenses, lab_exp_ratio),
        (3, '**Расходы на оплату труда**', labour_tax_free, ''),
        ('', 'в том числе:', '', ''),
        (4, 'преподаватель', teacher_salary, teach_sal_ratio),
        ('', 'АУП', '', ''),
        ('', 'в том числе:', '', ''),
        # admin salary rows
        *((5 + i,  # index
           key,  # position name
           admin_salaries[key][1],  # salary
           admin_salaries[key][0])  # percentage
          for i, key in enumerate(admin_salaries)),
        (5 + len(admin_salaries), '**Начисление налога (ЕСН 30,2%)**', labour_tax, ''),
        (6 + len(admin_salaries), '**Фонд учреждения**', indirect_costs, indir_cost_ratio),
        empty_row,
        ('', 'Итого расходов', sum((teacher_salary, *(admin_sal[1] for admin_sal in admin_salaries.values()),
                                    labour_tax, indirect_costs)), '')
    )
    return res


def create_report(est: str, head_title: str, head: str, club: str, teacher: str,
                  period: dict, data: tuple, accountant: str) -> fpdf.FPDF:
    b = 0  # to test with borders
    # setting up the pdf document
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_font(fname='fonts/times.ttf', family='TimesCyrillic')
    pdf.add_font(fname='fonts/timesbd.ttf', family='TimesCyrillic', style='B')
    pdf.add_font(fname='fonts/timesbi.ttf', family='TimesCyrillic', style='BI')
    pdf.add_font(fname='fonts/timesi.ttf', family='TimesCyrillic', style='I')
    pdf.add_page()
    pdf.set_font('TimesCyrillic', '', 11)
    pdf.set_margin(0)

    # printing the top right corner ('Confirmed by headmaster(name) etc.')
    pdf.set_xy(113, 25)
    pdf.cell(w=72, h=5, txt='Утверждаю', new_x='LEFT', new_y='NEXT', border=b)
    pdf.multi_cell(w=72, h=5, txt=f'\n{head_title.lower()} ' + est, new_x='LEFT', new_y='NEXT', border=b)
    pdf.cell(w=72, h=5, txt='', new_x='LEFT', new_y='NEXT', border=b)
    pdf.cell(w=36, h=5, txt='_' * 17 + '/', new_x='RIGHT', new_y='TOP', border=b)
    pdf.cell(w=36, h=5, txt=head if head is not None and len(head) > 0 else '_' * 15, new_x='LEFT', new_y='NEXT',
             border=b)
    pdf.set_xy(pdf.get_x() - 36, pdf.get_y())
    pdf.set_font_size(9)
    pdf.cell(w=36, h=5, txt='(подпись)', align='C', new_x='RIGHT', new_y='LAST', border=b)
    pdf.cell(w=36, h=5, txt='' if head is not None and len(head) > 0 else '(расшифровка)',
             align='C', border=b)
    # printing the middle part (heading of the report)
    pdf.set_xy(25, 85)
    pdf.set_font_size(11)
    pdf.cell(w=160, h=5, txt='**РАСЧЕТ**', markdown=True, align='C', new_x='LEFT', new_y='NEXT', border=b)
    start, fin = get_school_year(period["-MONTH_NUM-"], period["-YEAR-"])
    pdf.cell(w=160, h=5, txt=f'расхода по дополнительным платным услугам на {start}-{fin} учебный год',
             align='C', new_x='LEFT', new_y='NEXT', border=b)
    pdf.cell(w=160, h=5, txt=f'на кружок "{club}"', align='C', new_x='LEFT', new_y='NEXT', border=b)
    pdf.set_xy(25, 105)
    pdf.cell(w=13, h=5, txt=f'ПДО:', new_x='RIGHT', new_y='TOP', border=b)
    pdf.cell(w=75, h=5, txt=teacher, new_x='RIGHT', new_y='TOP', border=b)
    pdf.set_xy(pdf.get_x() + 32, pdf.get_y())
    pdf.cell(w=40, h=5, txt=f'за {period["-MONTH-"].lower()} {period["-YEAR-"]} года', align='L', border=b)
    # drawing the table itself
    pdf.set_xy(25, 115)
    line_height = pdf.font_size * 1.5
    col_widths = [13, 75, 32, 40]
    pdf.set_margin(25)
    for row in data:
        i = 0
        for datum in row:
            if isinstance(datum, float):  # formatting the numbers so that they look cool
                align_number_to_right = True
                if datum > 1:
                    datum = f'{datum:,.2f}'.replace(',', ' ').replace('.', ',')
                else:
                    datum = '%.0f' % (datum * 100) + '%'

            else:
                align_number_to_right = False
            pdf.multi_cell(col_widths[i], line_height, str(datum), markdown=True, border=1,
                           align='R' if align_number_to_right or isinstance(datum, int) else 'L',
                           new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
            i += 1
        pdf.ln(line_height)
    # drawing the signature
    pdf.set_margin(0)
    pdf.set_xy(38, pdf.get_y() + line_height)
    pdf.cell(w=75, h=5, txt='Расчет составил(а):', new_x='RIGHT', new_y='TOP', border=b)
    pdf.cell(w=32, h=5, txt='_' * 15, new_x='RIGHT', new_y='TOP', border=b)
    pdf.cell(w=40, h=5, txt=accountant, new_y='NEXT', border=b)
    pdf.set_font_size(9)
    pdf.set_xy(113, pdf.get_y())
    pdf.cell(w=32, h=5, txt='(подпись)', align='C', border=b)

    return pdf


if __name__ == '__main__':
    pass
