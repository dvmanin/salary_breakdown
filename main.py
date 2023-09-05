import PySimpleGUI as sg
import gui
import output_writer as out
import loader_saver as ls

ICON = b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAFiUAABYlAUlSJPAAAAD4SURBVEhLtY5bAoQgDAP3/pd2sc0i9hGKsvOh0oaJn6PAJwFrCgtBk4uwpk3xbnrNQPLBdEk9El60o8d2xV+/nV/aFSO5DlvsyqjC10Z7Y62grUYwndGT5yu7JkK7CochGksLuKXSwQrq9wkoeGZXKh0nOP3wk4xpUvT3kDlO4XnRvytoqKSDqZCPBrCoYfJqYAq+9Zi86GeKaaDjk6L/d4G+9JxR6Qjt57N/cXgm3K4VNFrMJ8OhonPsspBHhBeYOvpquaCILWhs7BhVN+mWDiOxxpcd/nqga6FnNeGtVLTUIb8U55lFrzVwdmBNf6X0m9A4sCYcxxf8iVU4DVIWXwAAAABJRU5ErkJggg=='
VERSION = '1.2'


def main():
    sg.theme('Purple')

    est_list = ls.get_establishment_list('est_list.json')
    est_names = [est.name for est in est_list]
    est_names.append('Новое учреждение...')

    top_layout = [
        [sg.P(), sg.T('Расчет расходов по платным услугам', font='default 14 bold'), sg.P()],
        [sg.T('Пожалуйста, введите все данные, затем нажмите на кнопку "Печать"')],
        [sg.T('Учреждение'), sg.P(), sg.Combo(est_names, size=43, key='-EST_NAME-', enable_events=True)],
        [sg.T('Директор', font='default 10 underline', enable_events=True, key='-HEAD_TITLE-', metadata='Директор'),
         sg.P(), sg.In(size=45, key='-HEAD_NAME-')],
        [sg.T('Месяц'), sg.P(), sg.T('', visible=False, key='-PERIOD-'), sg.P(),
         sg.B('Выбрать месяц', key='-SELECT_MONTH-')],
        [sg.T('Кружок'), sg.P(), sg.Combo([], size=43, disabled=True, key='-CLUB_NAME-', enable_events=True)],
        [sg.T('Педагог'), sg.P(), sg.In(size=45, key='-TEACHER_NAME-')],
        [sg.T('Составитель расчета'), sg.P(), sg.In(size=45, key='-SIGNATURE_NAME-')]
    ]
    col1_layout = [
        [sg.P(), sg.T('Введите расходы учреждения', font='default 12 bold'), sg.P()],
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
        [sg.P(), sg.T('Выберите разбивку средств на АУП', font='default 12 bold'), sg.P()],
        [sg.Table([], headings=['Должность', 'Процент'],
                  num_rows=5, key='-ADMIN_PERCENTAGES-', expand_x=True)],
        [sg.P(), sg.Button('Настроить распределение АУП', key='-DEFINE_ADMIN-')]
    ]
    col_top = sg.Column(top_layout)
    col1 = sg.Column(col1_layout)
    col2 = sg.Column(col2_layout)

    window = sg.Window('Расчет расходов кружка',
                       layout=[
                           [sg.Menu([['&Режим', ['&Проверить данные']],
                                     ['&Помощь', ['&О программе']]])],
                           [sg.P(), col_top, sg.P()],
                           [sg.HorizontalSeparator()],
                           [col1, sg.VSeparator(), col2],
                           [sg.B('Печать', key='-SAVE-'), sg.B('Выйти', key='-EXIT-')]
                       ], icon=ICON, grab_anywhere=True)

    date_values = None  # to save the period of the report
    transfer_admin_to_indir = None  # to save user's choice (raises a popup error later if None)
    admin_percentages = None  # to save admin breakdown (empty being the default option)
    curr_est = None
    club_names = None
    curr_club = None
    club_index = None

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, '-EXIT-'):  # the user quits the program
            break

        if event == 'О программе':
            prog_description = 'Программа расчета платных услуг\n' \
                               'для учреждений МКУ ЦБ МОУ г. Якутска' \
                               '\n\tv.{v}\n\n' \
                               'Манин Дмитрий, 2023\n\nКонтакты:' \
                               '\nE-mail: manindmi@gmail.com'.format(v=VERSION)
            sg.popup(prog_description, title='О программе', keep_on_top=True, icon=ICON)

        if event == 'Проверить данные':
            window.hide()
            gui.run_check_values_window()
            window.un_hide()

        if event == '-HEAD_TITLE-':
            new_title = 'Директор' if window['-HEAD_TITLE-'].metadata == 'Заведующий' else 'Заведующий'
            window['-HEAD_TITLE-'].update(value=new_title)
            window['-HEAD_TITLE-'].metadata = new_title
            window.refresh()

        if event == '-EST_NAME-':  # the user has chosen the school from the list
            if values['-EST_NAME-'] == 'Новое учреждение...':  # the user wants to create a new est
                ns_data = gui.run_new_school_window()
                if ns_data is None:  # the user just closed the "new school" window
                    curr_est = None
                    window['-EST_NAME-'].update(value='')
                    window['-CLUB_NAME-'].update(value='', disabled=True)
                    window['-HEAD_NAME-'].update(value='')
                    window['-SIGNATURE_NAME-'].update(value='')
                else:  # the user has decided to create a new school
                    curr_est = ls.Establishment(
                        name=ns_data['school_name'],
                        head_name=ns_data['head_name'],
                        accountant=ns_data['accountant'],
                        club_list=list()
                    )
                    est_list.append(curr_est)
                    est_names.insert(-1, curr_est.name)
                    club_names = ['Новый кружок...']
                    window['-EST_NAME-'].update(value=curr_est.name, values=est_names)
                    window['-CLUB_NAME-'].update(values=club_names, disabled=False)
                    window['-HEAD_NAME-'].update(value=curr_est.head_name)
                    window['-SIGNATURE_NAME-'].update(value=curr_est.accountant)
            else:  # the user has chosen a school from the list
                curr_est = est_list[est_names.index(values['-EST_NAME-'])]
                club_names = [club.name for club in curr_est.club_list]
                club_names.append('Новый кружок...')
                window['-CLUB_NAME-'].update(values=club_names, disabled=False)
                window['-HEAD_TITLE-'].update(value=curr_est.head_title)
                window['-HEAD_TITLE-'].metadata = curr_est.head_title
                window['-HEAD_NAME-'].update(value=curr_est.head_name)
                window['-SIGNATURE_NAME-'].update(value=curr_est.accountant)

            # all of these go to default for any new school or a school from the list
            curr_club = None
            admin_percentages = None
            transfer_admin_to_indir = None

            # flushes any information on the clubs, if any was entered
            for field in ('-TEACHER_NAME-', '-IN_TOTAL-', '-IN_LABOUR-', '-IN_TEACHER-', '-IN_ADMIN-',
                          '-IN_TRANSFERS-', '-IN_INDIRECT-', '-IN_TOTAL-', '-IN_REV-'):
                window[field].update(value='')
            window['-ADMIN_PERCENTAGES-'].update(values=[])
            window.refresh()

        if event == '-CLUB_NAME-':  # the user has chosen the club from the list
            if values['-CLUB_NAME-'] == 'Новый кружок...':  # the user wants to create a new club
                c_name = sg.popup_get_text('Введите название кружка (без кавычек)',
                                           modal=True, icon=ICON)
                if c_name is None:  # new window closed, no club entered
                    curr_club = None
                    window['-CLUB_NAME-'].update(value='')
                else:  # a new club has been registered
                    curr_club = ls.Club(name=c_name, teacher_name='')
                    club_names.insert(-1, c_name)
                    curr_est.club_list.append(curr_club)
                    club_index = len(curr_est.club_list) - 1
                    window['-CLUB_NAME-'].update(value=c_name, values=club_names)

                # all these go to default for any new club
                admin_percentages = None
                transfer_admin_to_indir = None
                window['-ADMIN_PERCENTAGES-'].update(values=[])
                for k in ['-IN_TOTAL-', '-IN_LABOUR-', '-IN_TEACHER-',
                          '-IN_ADMIN-', '-IN_TRANSFERS-', '-IN_INDIRECT-', '-IN_REV-',
                          '-TEACHER_NAME-']:
                    window[k].update(value='')

            else:  # user chose a club within the existing list
                club_index = club_names.index(values['-CLUB_NAME-'])
                curr_club = curr_est.club_list[club_index]
                admin_percentages = curr_club.admin_breakdown
                transfer_admin_to_indir = curr_club.transfer_admin_to_indir
                window['-IN_TOTAL-'].update(value=curr_club.total_expenses)
                window['-IN_LABOUR-'].update(value=curr_club.labour_expenses)
                window['-IN_TEACHER-'].update(value=curr_club.teacher_salary)
                window['-IN_ADMIN-'].update(value=curr_club.admin_salary)
                window['-IN_TRANSFERS-'].update(value=curr_club.transfers_labour)
                window['-IN_INDIRECT-'].update(value=curr_club.indirect_costs)
                if admin_percentages is not None:
                    window['-ADMIN_PERCENTAGES-'].update(values=zip(admin_percentages.keys(), admin_percentages.values()))
                else:
                    window['-ADMIN_PERCENTAGES-'].update(values=[])
                window['-TEACHER_NAME-'].update(value=curr_club.teacher_name)
                window['-IN_REV-'].update(value='')
            window.refresh()

        if event == '-SELECT_MONTH-':  # the user selects the month in a new window
            date_values = gui.run_period_input_window(date_values)
            if date_values is not None:
                window['-PERIOD-'].update(date_values['-MONTH-'] + ' ' + str(date_values['-YEAR-']), visible=True)
            window.refresh()

        if event == '-DEFINE_ADMIN-':  # the user chooses to set admin percentages
            admin_percentages, transfer_admin_to_indir = gui.run_admin_perc_window(admin_percentages,
                                                                                   transfer_admin_to_indir)
            if admin_percentages is not None:  # in case user has entered acceptable values
                window['-ADMIN_PERCENTAGES-'].update(values=zip(admin_percentages.keys(), admin_percentages.values()))
                window.refresh()

        if event == '-SAVE-':  # if the user finally decides to create the report
            if curr_est is None:  # user hasn't chosen an establishment
                sg.popup('Выберите учреждение или создайте новое', title='Ошибка', icon=ICON)
                continue
            if curr_club is None:  # user hasn't chosen a club
                sg.popup('Выберите кружок или создайте новый', title='Ошибка', icon=ICON)
                continue

            try:
                costs = gui.check_transform_costs([values['-IN_TOTAL-'],
                                                   values['-IN_LABOUR-'],
                                                   values['-IN_TEACHER-'],
                                                   values['-IN_ADMIN-'],
                                                   values['-IN_TRANSFERS-'],
                                                   values['-IN_INDIRECT-'],
                                                   values['-IN_REV-']])
            except ValueError:
                sg.popup('Проверьте полноту и правильность введенных расходов учреждения',
                         title='Ошибка', icon=ICON)
                continue
            except AssertionError as ae:
                sg.popup(ae, title='Ошибка', icon=ICON)
                continue

            # user hasn't picked the period of reporting
            if date_values is None:
                sg.popup('Заполните период отчетности', title='Ошибка', icon=ICON)
                continue
            # user hasn't entered the admin distribution
            if admin_percentages is None or transfer_admin_to_indir is None:
                sg.popup('Заполните распределение средств АУП', title='Ошибка', icon=ICON)
                continue

            x = ls.Club(name=values['-CLUB_NAME-'], teacher_name=values['-TEACHER_NAME-'],
                        period_revenue=costs[6],
                        total_expenses=costs[0], labour_expenses=costs[1], teacher_salary=costs[2],
                        admin_salary=costs[3], transfers_labour=costs[4], indirect_costs=costs[5],
                        transfer_admin_to_indir=transfer_admin_to_indir,
                        admin_breakdown={key: value.copy() for key, value in admin_percentages.items()})

            if x != curr_club:
                curr_est.club_list[club_index] = x
            if curr_est.name != values['-EST_NAME-']:
                curr_est.name = values['-EST_NAME-']
            if curr_est.head_title != window['-HEAD_TITLE-'].metadata:
                curr_est.head_title = window['-HEAD_TITLE-'].metadata
            if curr_est.head_name != values['-HEAD_NAME-']:
                curr_est.head_name = values['-HEAD_NAME-']
            if curr_est.accountant != values['-SIGNATURE_NAME-']:
                curr_est.accountant = values['-SIGNATURE_NAME-']
            ls.save_establishment_list('est_list.json', est_list)

            x.get_info_for_report()

            report_table = out.create_table(rev=x.period_revenue,
                                            labour_expenses=x.period_labour_expenses,
                                            labour_tax_free=x.period_labour_tax_free,
                                            teacher_salary=x.period_teacher_expenses,
                                            admin_salaries=x.admin_breakdown,
                                            labour_tax=x.period_tax,
                                            indirect_costs=x.period_indirect_costs,
                                            lab_exp_ratio=x.lab_exp_ratio,
                                            teach_sal_ratio=x.teach_sal_ratio,
                                            indir_cost_ratio=x.indir_cost_ratio)

            report = out.create_report(est=values['-EST_NAME-'],
                                       head_title=window['-HEAD_TITLE-'].metadata,
                                       head=values['-HEAD_NAME-'],
                                       club=x.name,
                                       teacher=x.teacher_name,
                                       period=date_values,
                                       data=report_table,
                                       accountant=values['-SIGNATURE_NAME-'])

            gui.run_save_window(report)

    window.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        from os.path import exists

        with open('crashlog.txt', 'w' if exists('./crashlog.txt') else 'x') as f:
            f.write(traceback.format_exc())
        sg.popup_ok('Извините, произошла чудовищная ошибка. Программа не может выполняться дальше.\nПожалуйста, '
                    'отправьте лог ошибки из файла crashlog.txt  в папке с программой,'
                    ' чтобы мы могли ее как можно быстрее исправить.', title='Простите...', icon=ICON)
