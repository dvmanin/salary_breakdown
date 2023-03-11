import PySimpleGUI as sg
import gui
import output_writer as out
import loader_saver as ls


def main():
    sg.theme('Purple')

    est_list = ls.get_establishment_list('est_list.json')
    est_names = [est.name for est in est_list]
    est_names.append('Новое учреждение...')

    top_layout = [
        [sg.P(), sg.T('Расчет расходов по платным услугам', font='default 14 bold'), sg.P()],
        [sg.T('Пожалуйста, введите все данные, затем нажмите на кнопку "Печать"')],
        [sg.T('Учреждение'), sg.P(), sg.Combo(est_names, size=43, key='-EST_NAME-', enable_events=True)],
        [sg.T('Директор'), sg.P(), sg.In(size=45, key='-HEAD_NAME-')],
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
        [sg.P(), sg.Table([], headings=['Должность', 'Процент'],
                          num_rows=5, key='-ADMIN_PERCENTAGES-'), sg.P()],
        [sg.P(), sg.Button('Настроить распределение АУП', key='-DEFINE_ADMIN-')]
    ]
    col_top = sg.Column(top_layout)
    col1 = sg.Column(col1_layout)
    col2 = sg.Column(col2_layout)

    window = sg.Window('Расчет расходов кружка',
                       layout=[
                           [sg.P(), col_top, sg.P()],
                           [sg.HorizontalSeparator()],
                           [col1, sg.VSeparator(), col2],
                           [sg.B('Печать', key='-SAVE-'), sg.B('Выйти', key='-EXIT-')]
                       ])

    date_values = None  # to save the period of the report
    transfer_admin_to_indir = None  # to save user's choice (raises a popup error later if None)
    admin_percentages = {}  # to save admin breakdown (empty be default)
    curr_est = None
    club_names = None
    curr_club = None
    club_index = None

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, '-EXIT-'):  # the user quits the program
            break

        if event == '-EST_NAME-':  # the user has chosen the school from the list
            if values['-EST_NAME-'] == 'Новое учреждение...':
                ns_data = gui.run_new_school_window()
                if ns_data is None:
                    window['-EST_NAME-'].update(value='')
                    for field in values.keys():
                        try:
                            window[field].update(value='')
                        except Exception:
                            pass
                    continue
                else:
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
            else:
                curr_est = est_list[est_names.index(values['-EST_NAME-'])]
                club_names = [club.name for club in curr_est.club_list]
                club_names.append('Новый кружок...')
            window['-CLUB_NAME-'].update(values=club_names, disabled=False)
            window['-HEAD_NAME-'].update(value=curr_est.head_name)
            window['-SIGNATURE_NAME-'].update(value=curr_est.accountant)

            # flushes any information on the clubs, if any was entered
            for field in ('-TEACHER_NAME-', '-IN_TOTAL-', '-IN_LABOUR-', '-IN_TEACHER-', '-IN_ADMIN-',
                          '-IN_TRANSFERS-', '-IN_INDIRECT-', '-IN_TOTAL-', '-IN_REV-'):
                window[field].update(value='')
            window.refresh()

        if event == '-CLUB_NAME-':  # the user has chosen the club from the list
            if values['-CLUB_NAME-'] == 'Новый кружок...':
                c_name = sg.popup_get_text('Введите название кружка')
                if c_name is None:
                    window['-CLUB_NAME-'].update(value='')
                    continue
                else:
                    curr_club = ls.Club(name=c_name, teacher_name='')
                    club_names.insert(-1, c_name)
                    curr_est.club_list.append(curr_club)
                    club_index = len(curr_est.club_list) - 1
                    window['-CLUB_NAME-'].update(value=c_name, values=club_names)
            else:
                club_index = club_names.index(values['-CLUB_NAME-'])
                curr_club = curr_est.club_list[club_index]
            window['-TEACHER_NAME-'].update(value=curr_club.teacher_name)
            window['-IN_TOTAL-'].update(value=curr_club.total_expenses)
            window['-IN_LABOUR-'].update(value=curr_club.labour_expenses)
            window['-IN_TEACHER-'].update(value=curr_club.teacher_salary)
            window['-IN_ADMIN-'].update(value=curr_club.admin_salary)
            window['-IN_TRANSFERS-'].update(value=curr_club.transfers_labour)
            window['-IN_INDIRECT-'].update(value=curr_club.indirect_costs)
            window.refresh()

        if event == '-SELECT_MONTH-':  # the user selects the month in a new window
            date_values = gui.run_period_input_window(date_values)
            if date_values is not None:
                window['-PERIOD-'].update(date_values['-MONTH-'] + ' ' + str(date_values['-YEAR-']), visible=True)
            window.refresh()

        if event == '-DEFINE_ADMIN-':  # the user chooses to set admin percentages
            admin_percentages, transfer_admin_to_indir = gui.run_admin_perc_window()
            if len(admin_percentages) > 0:  # in case user has entered acceptable values
                window['-ADMIN_PERCENTAGES-'].update(values=zip(admin_percentages.keys(), admin_percentages.values()))
                window.refresh()

        if event == '-SAVE-':  # if the user finally decides to create the report
            try:
                costs = gui.check_transform_costs(values['-IN_TOTAL-'],
                                                  values['-IN_LABOUR-'],
                                                  values['-IN_TEACHER-'],
                                                  values['-IN_ADMIN-'],
                                                  values['-IN_TRANSFERS-'],
                                                  values['-IN_INDIRECT-'],
                                                  values['-IN_REV-'])
            except ValueError:
                sg.popup('Проверьте полноту и правильность введенных расходов учреждения',
                         title='Ошибка')
                continue
            except AssertionError:
                sg.popup('Введенные расходы должны быть положительными',
                         title='Ошибка')
                continue

            # user hasn't picked the period of reporting
            if date_values is None:
                sg.popup('Заполните период отчетности', title='Ошибка')
                continue
            # user hasn't entered the admin distribution
            if len(admin_percentages) == 0 or transfer_admin_to_indir is None:
                sg.popup('Заполните распределение средств АУП', title='Ошибка')
                continue

            x = ls.Club(name=values['-CLUB_NAME-'], teacher_name=values['-TEACHER_NAME-'],
                        period_revenue=costs[6],
                        total_expenses=costs[0], labour_expenses=costs[1], teacher_salary=costs[2],
                        admin_salary=costs[3], transfers_labour=costs[4], indirect_costs=costs[5])

            if x != curr_club:
                curr_est.club_list[club_index] = x
            if curr_est.name != values['-EST_NAME-']:
                curr_est.name = values['-EST_NAME-']
            if curr_est.head_name != values['-HEAD_NAME-']:
                curr_est.head_name = values['-HEAD_NAME-']
            if curr_est.accountant != values['-SIGNATURE_NAME-']:
                curr_est.accountant = values['-SIGNATURE_NAME-']
            ls.save_establishment_list('est_list.json', est_list)

            x.get_info_for_report(admin_breakdown={key: value.copy() for key, value in admin_percentages.items()},
                                  transfer_admin_to_indir=transfer_admin_to_indir)

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
        sg.popup_ok('Извините, произошла чудовищная ошибка. Программа не может выполняться дальше.\nПожалуйста, '
                    'покажите скрин этого сообщения,'
                    ' чтобы мы могли ее как можно быстрее исправить.\n\n' + traceback.format_exc(), title='Простите...')
