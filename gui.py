import PySimpleGUI as sg
from datetime import date
import os

import fpdf


def check_transform_costs(*args) -> list:
    '''
    Checks whether the entered arguments are (strictly) positive floats
    :param args: a list of entered arguments (strings of floats !with decimal comma!)
    :return: the same list of arguments, but typecast as floats
    '''

    res = list()
    for arg in args:
        num_arg = float(arg.strip().lower().replace(',', '.'))
        assert num_arg > 0, 'non-positive costs entered'
        res.append(num_arg)
    return res


def run_admin_perc_window() -> (dict, bool):
    '''
    Runs the input window for distribution of admin salaries
    :return admin_percentages: dict: dict of type {'position_i': [perc_i]]}
            may return empty dict, in case the user hasn't entered anything and closed the window
            transfer_to_indirect: a bool that is True if user chose to redirect some funds to indirect costs
    '''
    apc = 0  # admin_people_count
    admin_percentages = {}  # to save the distribution (empty by default)
    transfer_to_indirect = None  # to save user's choice (None by default)

    admin_input_layout = [
        [sg.Checkbox('Перевести часть средств в фонд учреждения', key='-TRANSFER_ADMIN_TO_INDIR-',
                     enable_events=True),
         sg.In(size=3, disabled=True, key='-ADMIN_TO_INDIR_PERCENTAGE-'), sg.T('%')],
        [sg.Column([], key='-ADMIN_STAFF-')],
        [sg.Button('Добавить нового сотрудника', key='-NEW_PERSON-'), sg.Button('Сохранить')]
    ]
    admin_input_window = sg.Window('Настройка распределения АУП', admin_input_layout, modal=True)

    while True:
        event2, values2 = admin_input_window.read()

        if event2 == '-NEW_PERSON-':  # the user decides to create a new admin position

            # if previous person wasn't fully added, block the creation of new input rows
            if apc > 0 and (values2.get(f'pos{apc}') in ('', None) or values2.get(f'perc{apc}') in ('', None)):
                sg.popup('Заполните сначала имеющиеся поля', title='Ало')
                continue

            # adding a new input row
            apc += 1
            admin_input_window.extend_layout(
                admin_input_window['-ADMIN_STAFF-'],
                [[sg.T('Должность'), sg.In(size=22, key=f'pos{apc}'),
                  sg.T('Процент'), sg.In(size=3, key=f'perc{apc}'), sg.T('%')]]
            )

        if event2 == '-TRANSFER_ADMIN_TO_INDIR-':  # the user allows to set smth to indirect costs
            admin_input_window['-ADMIN_TO_INDIR_PERCENTAGE-'].update(
                disabled=not values2['-TRANSFER_ADMIN_TO_INDIR-'])
            admin_input_window.refresh()

        if event2 == sg.WIN_CLOSED:  # the user crudely closes the window (nothing is saved)
            admin_percentages.clear()  # returning an empty dict in case something was saved there
            break
        elif event2 == 'Сохранить':  # the user saves the changes and closes the window
            admin_percentages.clear()  # clears in case something was already saved
            total_perc = 0  # total sum of percentages (must be equal to 20)

            # saving all the inputs in the admin_percentages dict
            try:
                for i in range(apc):
                    assert values2.get(f'pos{i + 1}') not in ('', None) \
                           and values2.get(f'perc{i + 1}') not in ('', None)
                    values2[f'perc{i + 1}'] = int(values2[f'perc{i + 1}'])
                    admin_percentages[values2[f'pos{i + 1}']] = [values2[f'perc{i + 1}']]
                    total_perc += values2[f'perc{i + 1}']
            except AssertionError:  # if something wasn't entered, raises a popup error
                sg.popup('Проверьте заполнение всех полей', title='Внимание')
                continue
            except ValueError:  # if percentage wasn't added as an integer, raises a popup error
                sg.popup('Проверьте правильность заполнения процентов. Пожалуйста, заполните проценты целыми '
                         'положительными цислами', title='Внимание')
                continue

            # if some funds are transferred to indirect costs
            if values2['-TRANSFER_ADMIN_TO_INDIR-']:
                try:  # checking if they have been entered correctly
                    assert values2.get('-ADMIN_TO_INDIR_PERCENTAGE-') not in ('', None)
                    values2['-ADMIN_TO_INDIR_PERCENTAGE-'] = int(values2['-ADMIN_TO_INDIR_PERCENTAGE-'])
                except AssertionError:
                    sg.popup('Проверьте заполнение всех полей', title='Внимание')
                    continue
                except ValueError:
                    sg.popup('Проверьте правильность заполнения процентов. Пожалуйста, заполните проценты целыми '
                             'положительными цислами',
                             title='Внимание')
                    continue
                # if everything's okay, add them to the distribution
                admin_percentages['В фонд учреждения'] = [values2['-ADMIN_TO_INDIR_PERCENTAGE-']]
                transfer_to_indirect = True
                total_perc += values2['-ADMIN_TO_INDIR_PERCENTAGE-']
            else:
                transfer_to_indirect = False

            # checks whether total perc is not equal to 20, raises a popup error if that's the case
            if total_perc != 20:
                sg.popup('Сумма всех введенных процентов не равна 20', title='Внимание')
                continue
            break

    admin_input_window.close()
    return admin_percentages, transfer_to_indirect


def run_period_input_window(date_values=None) -> dict:
    '''
        Runs the input window for period of report
        :param date_values: dict of type {'-MONTH-': month_name(str), '-MONTH_NUM-': month(int), '-YEAR-': year(int)}
                period-defining dict that may be already entered (if that's not the first call) or empty
        :return date_values: period-defining dict (or an updated version of it)
    '''
    rus_month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль',
                       'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']  # for interface
    mth_num, mth, yr = date.today().month, rus_month_names[date.today().month - 1], date.today().year  # get today's date
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
    date_input_window = sg.Window('Введите период', date_input_layout, modal=True)
    event1, values1 = date_input_window.read()
    if event1 == 'OK':
        date_values = values1.copy()
        date_values['-MONTH_NUM-'] = rus_month_names.index(values1['-MONTH-']) + 1
        date_values['-YEAR-'] = int(date_values['-YEAR-'])
    date_input_window.close()
    return date_values


def run_save_window(report: fpdf.FPDF):
    save_window_layout = [
        [sg.T('Выберите путь для сохранения файла \nИли отправьте его на печать')],
        [sg.In(size=(45, 5), key='-STRING_PATH-'), sg.FileSaveAs(
            button_text='Обзор',
            file_types=(('Adobe Acrobat PDF', '.pdf'), ('Все файлы', '.*')),
            initial_folder=os.environ['HOMEPATH'],
            auto_size_button=True,
            key='-SAVE_FILE_PATH-'
        )],
        [sg.B('Сохранить файл', key='-SAVE-'), sg.Button('Печать', key='-PRINT-')]
    ]
    save_window = sg.Window(title='Отчет составлен', layout=save_window_layout)
    while True:
        event, values = save_window.read()
        if event == sg.WIN_CLOSED:
            break
        if event == '-SAVE-':
            if values['-STRING_PATH-'] in (None, ''):
                pass
            else:
                report.output(values['-STRING_PATH-'])
                sg.popup('Отчет сохранен в\n' + values['-STRING_PATH-'], title='Сохранено')
                break
        if event == '-PRINT-':
            report.output('temp/res.pdf')
            os.startfile(os.path.relpath('temp/res.pdf'), 'print')
            break
    save_window.close()


def run_new_school_window():
    res = None

    ns_layout = [
        [sg.T('Введите информацию в таком же виде, как в отчете')],
        [sg.T('Название'), sg.P(), sg.In(key='school_name')],
        [sg.T('Директор'), sg.P(), sg.In(key='head_name')],
        [sg.T('Бухгалтер'), sg.P(), sg.In(key='accountant')],
        [sg.B('Сохранить'), sg.B('Отмена')]
    ]
    ns_window = sg.Window(title='Новое учреждение', layout=ns_layout, modal=True)

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
                sg.popup('Данные не заполнены', title='Ошибка')
                continue
            res = values
            break

    ns_window.close()
    return res


if __name__ == '__main__':
    pass


















