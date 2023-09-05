import PySimpleGUI as sg
import os
import fpdf
from loader_saver import Club
from output_writer import create_table
from datetime import date
from math import isclose

ICON = b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAFiUAABYlAUlSJPAAAAD4SURBVEhLtY5bAoQgDAP3/pd2sc0i9hGKsvOh0oaJn6PAJwFrCgtBk4uwpk3xbnrNQPLBdEk9El60o8d2xV+/nV/aFSO5DlvsyqjC10Z7Y62grUYwndGT5yu7JkK7CochGksLuKXSwQrq9wkoeGZXKh0nOP3wk4xpUvT3kDlO4XnRvytoqKSDqZCPBrCoYfJqYAq+9Zi86GeKaaDjk6L/d4G+9JxR6Qjt57N/cXgm3K4VNFrMJ8OhonPsspBHhBeYOvpquaCILWhs7BhVN+mWDiOxxpcd/nqga6FnNeGtVLTUIb8U55lFrzVwdmBNf6X0m9A4sCYcxxf8iVU4DVIWXwAAAABJRU5ErkJggg=='


def check_transform_costs(cost_list: list) -> list:
    '''
    Checks whether the entered arguments are (strictly) positive floats. Also checks some additional requirements
    about the costs that should legally hold.
    :param cost_list: a list of entered arguments (strings of floats !with decimal comma!)
    :return: the same list of arguments, but typecast as floats
    '''

    cost_list = list(map(lambda x: float(x.strip().lower().replace(',', '.')), cost_list))
    for cost in cost_list:
        assert cost > 0, 'Введены неположительные расходы'

    assert isclose(cost_list[3],
                   0.2 * cost_list[2],
                   abs_tol=1), \
        'Не выполнено условие\nРасходы_АУП = 0,2 * Расходы_педагог'
    assert isclose(cost_list[4],
                   0.302 * (cost_list[2] + cost_list[3]),
                   abs_tol=1), \
        'Расходы ЕСН не равны 30,2% от суммы оплат труда'

    return cost_list


def run_admin_perc_window(admin_percentages: dict = None,
                          transfer_to_indirect: bool = None) -> (dict, bool):
    '''
    Runs the input window for distribution of admin salaries
    :return admin_percentages: dict: dict of type {'position_i': [perc_i]]}
            may return empty dict, in case the user hasn't entered anything and closed the window
            transfer_to_indirect: a bool that is True if user chose to redirect some funds to indirect costs
    '''
    if admin_percentages is None:
        admin_percentages = {}

    # admin_people_count
    apc = len(admin_percentages) if admin_percentages.get('В фонд учреждения') is None \
        else len(admin_percentages) - 1
    # admin personel percs as a tuple (without the transfer to indirect funds)
    ap = tuple(item for item in admin_percentages.items() if item[0] != 'В фонд учреждения')

    def create_row(row_counter, row_view_counter, def_name='', def_perc=''):
        row = [
            sg.pin(sg.Column([
                [sg.T('Должность'), sg.In(size=22, default_text=def_name, key=('-POS-', row_counter)),
                 sg.T('Процент'), sg.In(size=3, default_text=def_perc, key=('-PERC-', row_counter)),
                 sg.B('Удалить', key=('-DEL-', row_counter))]
            ],
                key=('-ROW-', row_counter), metadata={'n': row_counter, 'visible': True}))
        ]
        return row

    row_counter = 0
    row_number_view = 0
    prefilled_rows = []

    for item in ap:
        row_number_view += 1
        prefilled_rows.append(create_row(row_counter, row_number_view, item[0], item[1][0]))
        row_counter += 1

    admin_input_layout = [
        [sg.Checkbox('Перевести часть средств в фонд учреждения', key='-TRANSFER_ADMIN_TO_INDIR-',
                     enable_events=True, default=transfer_to_indirect),
         sg.In(size=3, disabled=False if transfer_to_indirect else True,
               default_text=admin_percentages['В фонд учреждения'][0] if transfer_to_indirect else '',
               key='-ADMIN_TO_INDIR_PERCENTAGE-'), sg.T('%')],
        [sg.Column(prefilled_rows, key='-ROW_PANEL-')],
        [sg.Button('Добавить нового сотрудника', key='-NEW_PERSON-'), sg.Button('Сохранить', key='-SAVE-')]
    ]

    admin_input_window = sg.Window('Настройка распределения АУП', admin_input_layout,
                                   modal=True, icon=ICON)

    while True:
        event, values = admin_input_window.read()

        if event == sg.WIN_CLOSED:
            break

        if event == '-TRANSFER_ADMIN_TO_INDIR-':  # the user allows to set smth to indirect costs
            admin_input_window['-ADMIN_TO_INDIR_PERCENTAGE-'].update(
                value='', disabled=not values['-TRANSFER_ADMIN_TO_INDIR-'])
            admin_input_window.refresh()

        if event == '-NEW_PERSON-':
            j = 0
            restored_row = False
            while j < row_counter:
                if not admin_input_window[('-ROW-', j)].metadata['visible']:
                    admin_input_window[('-ROW-', j)].metadata['visible'] = True
                    admin_input_window[('-ROW-', j)].update(visible=True)
                    restored_row = True
                    break
                j += 1
            if restored_row:
                row_number_view += 1
                admin_input_window.refresh()
                continue

            row_number_view += 1
            admin_input_window.extend_layout(admin_input_window['-ROW_PANEL-'],
                                             [create_row(row_counter, row_number_view)])
            row_counter += 1
            admin_input_window.refresh()

        if event[0] == '-DEL-':
            row_number_view -= 1
            admin_input_window[('-ROW-', event[1])].metadata['visible'] = False
            for j in ('-POS-', '-PERC-'):
                admin_input_window[(j, event[1])].update(value='')
            admin_input_window[('-ROW-', event[1])].update(visible=False)
            admin_input_window.refresh()

        if event == '-SAVE-':
            total_perc = 0
            res = {}

            try:
                for j in range(row_counter):
                    if admin_input_window[('-ROW-', j)].metadata['visible']:
                        assert values[('-POS-', j)] != '', 'Проверьте заполнение всех полей'
                        assert values[('-PERC-', j)] != '', 'Проверьте заполнение всех полей'
                        assert values[('-PERC-',
                                       j)].isdigit(), 'Проверьте правильность заполнения процентов: это должны быть целые положительные числа'
                        assert int(values[('-PERC-',
                                           j)]) > 0, 'Проверьте правильность заполнения процентов: это должны быть целые положительные числа'
                        res[values[('-POS-', j)]] = [int(values[('-PERC-', j)])]
                        total_perc += int(values[('-PERC-', j)])

                if values['-TRANSFER_ADMIN_TO_INDIR-']:
                    assert values['-ADMIN_TO_INDIR_PERCENTAGE-'] != '', 'Проверьте заполнение всех полей'
                    assert values[
                        '-ADMIN_TO_INDIR_PERCENTAGE-'].isdigit(), 'Проверьте правильность заполнения процентов: это должны быть целые положительные числа'
                    assert int(values[
                                   '-ADMIN_TO_INDIR_PERCENTAGE-']) > 0, 'Проверьте правильность заполнения процентов: это должны быть целые положительные числа'
                    res['В фонд учреждения'] = [int(values['-ADMIN_TO_INDIR_PERCENTAGE-'])]
                    total_perc += int(values['-ADMIN_TO_INDIR_PERCENTAGE-'])

                assert total_perc == 20, 'Сумма всех введенных процентов должна равняться 20'
            except AssertionError as ae:
                sg.popup(ae, title='Внимание', icon=ICON)
                continue

            admin_percentages = res
            transfer_to_indirect = values['-TRANSFER_ADMIN_TO_INDIR-']
            break

    if len(admin_percentages) == 0:
        admin_percentages = None

    admin_input_window.close()
    return admin_percentages, transfer_to_indirect


def run_period_input_window(date_values: dict = None) -> dict:
    '''
        Runs the input window for period of report
        :param date_values: dict of type {'-MONTH-': month_name(str), '-MONTH_NUM-': month(int), '-YEAR-': year(int)}
                period-defining dict that may be already entered (if that's not the first call) or empty
        :return date_values: period-defining dict (or an updated version of it)
    '''
    rus_month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль',
                       'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']  # for interface
    # get today's date
    mth_num, mth, yr = date.today().month, rus_month_names[date.today().month - 1], date.today().year
    # creating a new window with the following layout
    date_input_layout = [
        [sg.Text('Введите период, за который необходимо составить отчетность')],
        [sg.OptionMenu(rus_month_names,
                       default_value=mth if date_values is None else date_values['-MONTH-'],
                       key='-MONTH-'),
         sg.OptionMenu([i for i in range(yr - 4, yr + 1)],
                       default_value=yr if date_values is None else date_values['-YEAR-'],
                       key='-YEAR-')],
        [sg.Button('OK')]
    ]
    date_input_window = sg.Window('Введите период', date_input_layout, modal=True, icon=ICON)
    event1, values1 = date_input_window.read()
    if event1 == 'OK':
        date_values = values1.copy()
        date_values['-MONTH_NUM-'] = rus_month_names.index(values1['-MONTH-']) + 1
        date_values['-YEAR-'] = int(date_values['-YEAR-'])
    date_input_window.close()
    return date_values


def run_save_window(report: fpdf.FPDF):
    '''
    Runs a separate window, where the user chooses the path to save the PDF-file
    :param report: an object of class fpdf.FPDF - the report itself
    No reutrn
    '''
    save_window_layout = [
        [sg.T('Выберите путь для сохранения файла \nИли отправьте его на печать')],
        [sg.In(size=(45, 5), key='-STRING_PATH-'), sg.FileSaveAs(
            button_text='Обзор',
            file_types=(('Adobe Acrobat PDF', '.pdf'), ('Все файлы', '.*')),
            initial_folder=os.environ['HOMEPATH'],
            auto_size_button=True,
            key='-SAVE_FILE_PATH-'
        )],
        [sg.B('Сохранить файл', key='-SAVE-')]
    ]
    save_window = sg.Window(title='Отчет составлен', layout=save_window_layout,
                            icon=ICON, modal=True)
    while True:
        event, values = save_window.read()
        if event == sg.WIN_CLOSED:
            break
        if event == '-SAVE-':
            if values['-STRING_PATH-'] in (None, ''):
                pass
            else:
                report.output(values['-STRING_PATH-'])
                sg.popup('Отчет сохранен в\n' + values['-STRING_PATH-'], title='Сохранено', icon=ICON)
                break
    save_window.close()


def run_new_school_window():
    '''
    Runs a separate window, where the user inputs the data on a new school they want to register
    :return res: a dict consisting of school's name, headmaster's name, and the accountant's name
    '''
    res = None

    ns_layout = [
        [sg.T('Введите информацию в таком же виде, как в отчете')],
        [sg.T('Название'), sg.P(), sg.In(key='school_name')],
        [sg.T('Руководитель'), sg.P(), sg.In(key='head_name')],
        [sg.T('Составитель отчета'), sg.P(), sg.In(key='accountant')],
        [sg.B('Сохранить'), sg.B('Отмена')]
    ]
    ns_window = sg.Window(title='Новое учреждение', layout=ns_layout, modal=True, icon=ICON)

    while True:
        event, values = ns_window.read()

        if event in (sg.WIN_CLOSED, 'Отмена'):
            break

        if event == 'Сохранить':
            try:
                assert values['school_name'] not in (None, '')
                assert values['head_name'] not in (None, '')
                assert values['accountant'] not in (None, '')
            except AssertionError:
                sg.popup('Данные не заполнены', title='Ошибка', icon=ICON)
                continue
            res = values
            break

    ns_window.close()
    return res


def run_check_values_window():
    '''
    Runs the window that allows the user to simply check the values computed in the report, without taking any
    names of schools, clubs, etc. This mode doesn't save any input data and doesn't produce the PDF file.
    The output is shown on screen instead.
    '''
    col1_layout = [
        [sg.P(), sg.T('Расходы учреждения', font='default 12 bold'), sg.P()],
        [sg.T('Общие расходы:'), sg.P(), sg.In(size=15, key='-IN_TOTAL-')],
        [sg.T('Расходы на оплату труда:'), sg.P(), sg.In(size=15, key='-IN_LABOUR-')],
        [sg.T('Оплата труда педагога:'), sg.P(), sg.In(size=15, key='-IN_TEACHER-')],
        [sg.T('Оплата труда АУП:'), sg.P(), sg.In(size=15, key='-IN_ADMIN-')],
        [sg.T('Начисления на оплату труда:'), sg.P(), sg.In(size=15, key='-IN_TRANSFERS-')],
        [sg.T('Косвенные затраты:'), sg.P(), sg.In(size=15, key='-IN_INDIRECT-')],
        [sg.HSeparator()],
        [sg.T('Доходы кружка за период'), sg.P(), sg.In(size=15, key='-IN_REV-')]
    ]
    col2_layout = [
        [sg.P(), sg.T('Разбивка средств на АУП', font='default 12 bold'), sg.P()],
        [sg.Table([], headings=['Должность', 'Процент'],
                  num_rows=5, key='-ADMIN_PERCENTAGES-', expand_x=True)],
        [sg.P(), sg.Button('Настроить распределение АУП', key='-DEFINE_ADMIN-')]
    ]

    col1 = sg.Column(col1_layout)
    col2 = sg.Column(col2_layout)

    check_values_window = sg.Window('Режим проверки данных',
                                    layout=[
                                        [col1, sg.VSeparator(), col2],
                                        [sg.B('Рассчитать', key='-COMPUTE-')]
                                    ], icon=ICON)

    admin_percentages = {}
    transfer_admin_to_indir = None

    while True:
        event, values = check_values_window.read()

        if event == sg.WIN_CLOSED:
            break

        if event == '-DEFINE_ADMIN-':
            admin_percentages, transfer_admin_to_indir = run_admin_perc_window(admin_percentages,
                                                                               transfer_admin_to_indir)
            if len(admin_percentages) > 0:
                check_values_window['-ADMIN_PERCENTAGES-'].update(values=zip(admin_percentages.keys(),
                                                                             admin_percentages.values()))
                check_values_window.refresh()

        if event == '-COMPUTE-':
            try:
                costs = check_transform_costs([values['-IN_TOTAL-'],
                                               values['-IN_LABOUR-'],
                                               values['-IN_TEACHER-'],
                                               values['-IN_ADMIN-'],
                                               values['-IN_TRANSFERS-'],
                                               values['-IN_INDIRECT-'],
                                               values['-IN_REV-']])
                assert len(
                    admin_percentages) > 0 and transfer_admin_to_indir is not None, 'Заполните распределение средств АУП'
            except ValueError:
                sg.popup('Проверьте полноту и правильность введенных расходов учреждения',
                         title='Внимание', icon=ICON)
                continue
            except AssertionError as ae:
                sg.popup(ae, title='Внимание', icon=ICON)
                continue

            x = Club(period_revenue=costs[6],
                     total_expenses=costs[0], labour_expenses=costs[1], teacher_salary=costs[2],
                     admin_salary=costs[3], transfers_labour=costs[4], indirect_costs=costs[5],
                     transfer_admin_to_indir=transfer_admin_to_indir,
                     admin_breakdown={key: value.copy() for key, value in admin_percentages.items()})
            x.get_info_for_report()

            def transform_datum(datum):
                if isinstance(datum, str):
                    if datum == '':
                        return datum
                    if datum[0] == '*':
                        return datum.strip('*')
                if isinstance(datum, float):
                    if datum > 1:
                        return f'{datum:,.2f}'.replace(',', ' ').replace('.', ',')
                    else:
                        return '%.0f' % (datum * 100) + '%'
                return datum

            report_table = [list(map(transform_datum, row))
                            for row in create_table(rev=x.period_revenue,
                                                    labour_expenses=x.period_labour_expenses,
                                                    labour_tax_free=x.period_labour_tax_free,
                                                    teacher_salary=x.period_teacher_expenses,
                                                    admin_salaries=x.admin_breakdown,
                                                    labour_tax=x.period_tax,
                                                    indirect_costs=x.period_indirect_costs,
                                                    lab_exp_ratio=x.lab_exp_ratio,
                                                    teach_sal_ratio=x.teach_sal_ratio,
                                                    indir_cost_ratio=x.indir_cost_ratio)]

            res_layout = [
                [sg.Table(values=report_table[1:], headings=report_table[0], justification='left',
                          expand_x=True, expand_y=True, border_width=1)]
            ]
            res_window = sg.Window(layout=res_layout, title='Результат', size=(600, 300),
                                   resizable=True, keep_on_top=True, modal=True, icon=ICON)
            while True:
                res_event, _ = res_window.read()
                if res_event == sg.WIN_CLOSED:
                    break
            res_window.close()

    check_values_window.close()


if __name__ == '__main__':
    pass
