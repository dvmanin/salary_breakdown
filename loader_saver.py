import json
from os.path import exists


class Club:
    '''
    The class for a particular club.
    Used for
        (a) storing information on it in the JSON file;
        (b) computing all the necessary values for the report (with get_info_for_report method)
    '''
    def __init__(self, name='', teacher_name='',
                 period_revenue=0.0,
                 total_expenses=0.0, labour_expenses=0.0, teacher_salary=0.0,
                 admin_salary=0.0, transfers_labour=0.0, indirect_costs=0.0):
        self.name = name
        self.teacher_name = teacher_name
        self.period_revenue = period_revenue
        self.admin_breakdown = None

        # все 6 показателей расходов со страницы "расчет экономистов" (по умолчанию 0)
        self.total_expenses = total_expenses  # расходы учреждения
        self.labour_expenses = labour_expenses  # расходы на оплату труда
        self.teacher_salary = teacher_salary  # оплата труда педагог
        self.admin_salary = admin_salary  # оплата труда АУП
        self.transfers_labour = transfers_labour  # начисления на оплату труда
        self.indirect_costs = indirect_costs  # косвенные затраты

        # все 5 долей расходов со страницы "расчет экономистов" (по умолчанию 0.0)
        self.lab_exp_ratio = 0.0  # расходы на оплату труда
        self.teach_sal_ratio = 0.0  # оплата труда педагог
        self.admin_sal_ratio = 0.0  # оплата труда АУП
        self.trans_labour_ratio = 0.0  # начисления на оплату труда
        self.indir_cost_ratio = 0.0  # косвенные затраты
        self.period_labour_expenses = None
        self.period_labour_tax_free = None
        self.period_teacher_expenses = None
        self.period_tax = None
        self.period_indirect_costs = None

    def __eq__(self, other):
        return self.name == other.name and self.teacher_name == other.teacher_name \
            and self.total_expenses == other.total_expenses and self.labour_expenses == other.labour_expenses \
            and self.teacher_salary == other.teacher_salary and self.admin_salary == other.admin_salary \
            and self.transfers_labour == other.transfers_labour and self.indirect_costs == other.indirect_costs

    def calc_lab_exp_ratio(self):
        assert self.total_expenses > 0
        self.lab_exp_ratio = (self.labour_expenses + self.transfers_labour) / self.total_expenses

    def calc_teach_sal_ratio(self):
        assert self.labour_expenses > 0
        self.teach_sal_ratio = self.teacher_salary / self.labour_expenses

    def calc_admin_sal_ratio(self):
        assert self.teacher_salary > 0
        self.admin_sal_ratio = self.admin_salary / self.teacher_salary

    def calc_trans_labour_ratio(self):
        assert self.labour_expenses > 0
        self.trans_labour_ratio = self.transfers_labour / self.labour_expenses

    def calc_indir_cost_ratio(self):
        assert self.total_expenses > 0
        self.indir_cost_ratio = self.indirect_costs / self.total_expenses

    def get_info_for_report(self, admin_breakdown=None, transfer_admin_to_indir=None):
        # разбивка оплаты труда АУП по категориям (вводится пользователем)
        if transfer_admin_to_indir:
            amount_transferred = (admin_breakdown['В фонд учреждения'][0] /
                                  sum([v[0] for v in admin_breakdown.values()])) * self.admin_salary
            self.admin_salary -= amount_transferred
            self.labour_expenses = self.teacher_salary + self.admin_salary
            self.transfers_labour = self.labour_expenses * 0.302
            self.indirect_costs += amount_transferred * 1.302
            admin_breakdown.pop('В фонд учреждения', None)
        self.admin_breakdown = admin_breakdown

        # подсчет всех долей
        self.calc_lab_exp_ratio()
        self.calc_teach_sal_ratio()
        self.calc_admin_sal_ratio()
        self.calc_trans_labour_ratio()
        self.calc_indir_cost_ratio()

        self.period_labour_expenses = self.period_revenue * self.lab_exp_ratio
        self.period_labour_tax_free = self.period_labour_expenses / 1.302
        self.period_teacher_expenses = self.period_labour_tax_free * self.teach_sal_ratio
        self.period_indirect_costs = self.period_revenue * self.indir_cost_ratio
        self.period_tax = self.period_labour_tax_free * 0.302
        total_admin_perc = sum([v[0] for v in self.admin_breakdown.values()])
        for key in self.admin_breakdown.keys():
            self.admin_breakdown[key][0] = (self.admin_breakdown[key][0] / total_admin_perc) * self.admin_sal_ratio
            self.admin_breakdown[key].append(self.admin_breakdown[key][0] * self.period_teacher_expenses)


class Establishment:
    '''
    The class for an establishment (i.e. school).
    Used for loading/storing information to/from a JSON file.
    Contains (a) name of a school; (b) headmaster/accountant names; (c) list of all known clubs.
    '''
    def __init__(self, name='',
                 head_name='',
                 accountant='',
                 club_list=None):
        self.name = name
        self.head_name = head_name
        self.accountant = accountant
        self.club_list = club_list


class EstEncoder(json.JSONEncoder):
    '''
    Overriding standart JSONEncoder for the purposes of storing information on an Establishment
    '''
    def default(self, est):
        if isinstance(est, Establishment):
            return {'__est__': True,
                    'est_name': est.name,
                    'head_name': est.head_name,
                    'accountant': est.accountant,
                    'club_list': {club.name: (club.teacher_name,
                                              club.total_expenses,
                                              club.labour_expenses,
                                              club.teacher_salary,
                                              club.admin_salary,
                                              club.transfers_labour,
                                              club.indirect_costs)
                                  for club in est.club_list}
                    }
        else:
            return super().default(est)


def decode_est(obj):
    '''
    Function to decode the Establishment object in the JSON file.
    :param obj: any JSON object. Only processed by this function if contains '__est__': True item.
    :return: (a) if obj['__est__']==True: object of class Establishment with all the data from the file;
             (b) otherwise: obj itself to be processed into regular Python dict.
    '''
    if '__est__' in obj and obj['__est__']:
        return Establishment(name=obj['est_name'],
                             head_name=obj['head_name'],
                             accountant=obj['accountant'],
                             club_list=[Club(name=name,
                                             teacher_name=info[0],
                                             total_expenses=info[1],
                                             labour_expenses=info[2],
                                             teacher_salary=info[3],
                                             admin_salary=info[4],
                                             transfers_labour=info[5],
                                             indirect_costs=info[6])
                                        for name, info in obj['club_list'].items()])
    return obj


def get_establishment_list(filepath: str):
    '''
    Reads the JSON file with the establishment list
    :param filepath: path to a JSON file
    :return: est_list: list of objects of class Establishment
    '''
    if not exists(filepath):
        return []

    with open(filepath, 'r') as json_file:
        est_list = json.load(json_file, object_hook=decode_est)
    json_file.close()
    return est_list


def save_establishment_list(filepath: str, est_list: list):
    '''
    Saves the list of objects of class Establishment to a JSON file
    :param filepath: path to JSON file
    :param est_list: list of objects of class Establishment
    :return: True if the function was executed successfully
    '''
    with open(filepath, 'w') as json_file:
        json.dump(est_list, json_file, cls=EstEncoder)
    json_file.close()
    return True


if __name__ == '__main__':
    pass

    # c = Club(name='ИЗО деятельность',
    #          teacher_name='Александрова Наталия Павловна',
    #          total_expenses=81302.31,
    #          labour_expenses=45838.,
    #          teacher_salary=38198.,
    #          admin_salary=7640.,
    #          transfers_labour=13843.08,
    #          indirect_costs=21621.24)
    #
    # x = Establishment('МБДОУ Д/с № 14 "Журавлик" ГО "город Якутск"',
    #                   'Герасимова Л.Н.',
    #                   'Иванова М.П.',
    #                   [c])
    #
    # est_list = [x]
    #
    # with open('est_list.json', 'w') as output_file:
    #     json.dump(est_list, output_file, cls=EstEncoder, indent='\t')

    # with open('est_list.json', 'r') as input_file:
    #     ass = json.load(input_file, object_hook=decode_est)
    #
    # print(ass)
    # print(type(ass), len(ass))
    # print(ass[0].name)
    # print(ass[0].head_name)
    # print(ass[0].accountant)
    # print(ass[0].club_list)

