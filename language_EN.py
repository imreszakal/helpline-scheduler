filename = 'data_EN.csv'
after_year = ''
month_name_dic = {1:'January', 2:'February', 3:'March', 4:'April',
    5:'May', 6:'June', 7:'July', 8:'August', 9:'September',
    10:'October', 11:'November', 12:'December'}
l_C = 'C'
l_CP = 'CP'
l_P = 'P'
l_O = 'O'
l_Day = 'Day'
l_Phone = 'Phone'
l_Chat = 'Chat'
l_Observer = 'Observer'
l_phone = 'phone'
l_chat = 'chat'
l_observer = 'observer'
l_workloads = 'Workloads'
l_capacity = 'Workloads match originally offered capacity'
l_works_a = 'works'
l_works_b = ''
def l_day_maybe_plural(day):
    if day > 1:
        return 'days'
    else:
        return 'day'
l_but_offered_a = 'but offered'
l_but_offered_b = ''