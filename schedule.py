# https://github.com/imreszakal/helpline_scheduler

from ortools.sat.python import cp_model
import csv
import calendar

def main():
    # Get data from csv file
    f = []
    with open("schedule.csv") as csvfile:
         reader = csv.reader(csvfile, delimiter=',')
         for row in reader:
             f.append(row)
    schedule_year = int(f[0][0])
    schedule_month = int(f[1][0])
    month_name = calendar.month_name[schedule_month]
    data_first = 3
    data_last = len(f) - 1

    number_of_volunteers = len(f) - 3
    # Volunteers ID list [0,1,2,3,...]
    volunteers = [i for i in range(number_of_volunteers)]

    # Days in month; firstday 0 if monday
    firstday, days_in_month = calendar.monthrange(schedule_year, schedule_month)
    # Days' list [1,2,3,...]
    list_of_days = [i for i in range(1, days_in_month + 1)]
    # First Monday of the month
    first_monday = firstday + 1

    # Chat days' list (Mondays and Wednesdays)
    chat_days = []
    m, w = first_monday, first_monday + 2
    # Mondays
    while m <= days_in_month:
        chat_days.append(m)
        m += 7
    # Wednesdays
    while w <= days_in_month:
        chat_days.append(w)
        w += 7

    # Weekend days (Saturdays and Sundays)
    weekend_days = []
    sat, sun = first_monday + 5, first_monday + 6
    # Mondays
    while sat <= days_in_month:
        weekend_days.append(sat)
        sat += 7
    # Wednesdays
    while sun <= days_in_month:
        weekend_days.append(sun)
        sun += 7

    # Separate lists for each week
    m = first_monday
    week_count = 0
    if m != 1:
        week_count +=1
    days = days_in_month
    while days > 0:
        week_count += 1
        days -= 7
    weeks = [list() for i in range(week_count)]
    week_index = 0
    d = 1
    while d <= days_in_month:
        while (d - m) / 7 < 1 and d <= days_in_month:
            weeks[week_index].append(d)
            d += 1
        week_index += 1
        m += 7

    # Distance between workdays per person
    distance = 2


    # Phone: shift 0, Chat: shift 1, Observation: shift 2
    shifts = [0,1,2]

    # Creates the model.
    model = cp_model.CpModel()

    # Creates shift variables.
    # schedule[(v, d, s)]: volunteer 'v' works shift 's' on day 'd'.
    schedule = {}
    for v in volunteers:
        for d in list_of_days:
            for s in shifts:
                i = 'shift_{:_>2}.{:_>2}.{}'.format(v, d, s)
                schedule[(v, d, s)] = model.NewBoolVar(i)

    # Sets up class to processes input data
    def use_volunteer_data(id, type, days_available, workload,
        max_weekend_days, welcomes_observer, separate_w, alone,
        cannot_alone, not_with):

        all_days_available.append(days_available)
        all_workload.append(workload)

        # Volunteers doing only chat
        if type == 'C':
            for d in list_of_days:
                for s in [0,2]:
                    model.Add(schedule[(id, d, s)] == False)
                if d in days_available:
                    model.Add(schedule[(id, d, 1)] <= 1)
                else:
                    model.Add(schedule[(id, d, 1)] == False)

        # Volunteers doing chat and phone
        if type == 'CP':
            for d in list_of_days:
                model.Add(schedule[(id, d, 2)] == False)
                if d in days_available:
                    model.Add(sum(schedule[(id, d, s)]
                            for s in [0,1]) <= 1)
                else:
                    for s in [0,1]:
                        model.Add(schedule[(id, d, s)] == False)

        # Volunteers doing only phone
        if type == 'P':
            for d in list_of_days:
                for s in [1,2]:
                    model.Add(schedule[(id, d, s)] == False)
                if d in days_available:
                    model.Add(schedule[(id, d, 0)] <= 1)
                else:
                    model.Add(schedule[(id, d, 0)] == False)

        # Volunteers doing observation
        if type == 'O':
            observers.append(id)
            for d in list_of_days:
                for s in [0,1]:
                    model.Add(schedule[(id, d, s)] == False)
                if d in days_available:
                    model.Add(schedule[(id, d, 2)] <= 1)
                else:
                    model.Add(schedule[(id, d, 2)] == False)

        # List observers and volunteers welcoming observers
        if type in ['C', 'CP', 'P'] and welcomes_observer:
            welcomers.append(id)

        # Total workload
        model.Add(sum(schedule[(id, d, s)]
            for d in days_available for s in shifts) <= workload)

        # Max weekend days
        max_weekend_days
        days = [d for d in weekend_days if d in days_available]
        model.Add(sum(schedule[(id, d, s)]
            for d in days for s in shifts) <= max_weekend_days)

        # Wants shifts to be on different weeks
        if separate_w:
            for week in weeks:
                model.Add(sum(schedule[(id, d, s)]
                    for s in shifts for d in week
                    if d in days_available) <= 1)

        # Wants to work alone
        if alone:
            days = [d for d in days_available]
            others = [i for i in volunteers if i != id]
            for d in days:
                model.Add(sum(schedule[(v, d, s)] for v in others
                    for s in shifts) + schedule[(id, d, s)] <= 1)

        # Cannot work alone
        if cannot_alone:
            cannot_work_alone.append(id)

        # Does not want to work with XY
        if not_with:
            not_with_them.append([id, not_with])


    all_days_available = []
    all_workload = []
    all_cannot_alone = []
    all_not_with = []

    # List of volunteers welcoming observers and list of observers:
    welcomers = []
    observers = []

    # List of volunteers who cannot work alone
    cannot_work_alone = []

    # List of volunteer who does not want to work with some others
    not_with_them = []


    # Processing file data

    # volunteer_dic = {ID:name}, volunteer_dic_r = {name:ID}
    volunteer_dic = {}
    volunteer_dic_r = {}
    i = data_first
    while i <= data_last:
        volunteer_dic[i-3] = f[i][0]
        volunteer_dic_r[f[i][0]] = i-3
        i += 1

    def bool_from_string(value):
        bool(int(value))

    i = data_first
    while i <= data_last:
        id = i-3
        values = [x for x in f[i]]
        type = values[1]

        days_available = [int(x) for x in values[2].split(',')
            if x.strip().isdigit()]

        workload = int(values[3])
        max_weekend_days = int(values[4])

        welcomes_observer = bool_from_string(values[5])
        separate_w = bool_from_string(values[6])
        alone = bool_from_string(values[7])
        cannot_alone = bool_from_string(values[8])

        not_with = [volunteer_dic_r[name] for name in values[9].split(',')
            if name]

        use_volunteer_data(id, type, days_available, workload,
            max_weekend_days, welcomes_observer, separate_w, alone,
            cannot_alone, not_with)
        i += 1


    # Adding more constraints

    # Maximum one volunteer per shift.
    for d in list_of_days:
        # Phone shifts every day
        model.Add(sum(schedule[(v, d, 0)] for v in volunteers) <= 1)
        # Chat shifts on chat days
        if d in chat_days:
            model.Add(sum(schedule[(v, d, 1)] for v in volunteers) <= 1)
        # No chat shift for other days
        else:
            for v in volunteers:
                model.Add(schedule[(v, d, 1)] == False)

    # At least four days between shifts per volunteer
    for v in volunteers:
        days = list_of_days
        for day in days:
            a = day-distance
            b = day+distance
            while a < 1:
                a += 1
            while b > days_in_month:
                b -= 1
            model.Add(sum(schedule[(v, d, s)]
                for s in shifts for d in range(a, b + 1)) <= 1)

    # Observers only work with volunteers they are welcomed by
    for day in list_of_days:
        for o in observers:
            for v in volunteers:
                if v in welcomers:
                    model.Add(schedule[(o, d, 2)] <=
                        sum(schedule[(v, d, s)] for s in [0,1]))
                else:
                    for s in [0,1]:
                        model.Add((schedule[(o, d, 2)] and
                            schedule[(v, d, s)]) <= 1)
 
    # Cannot work alone
    for id in all_cannot_alone:
        days = [d for d in all_days_available[id]]
        others = [i for i in volunteers if i != id
            and i not in cannot_work_alone]
        other_not_alones = [i for i in cannot_work_alone if i != id]
        for d in days:
            # Only can work on a day when other volunteer works who
            # can work alone
            model.Add(sum(schedule[(id, d, s)] for s in shifts) <=
                sum(schedule[(v, d, s)]
                for v in others for s in shifts))
            # Cannot work on the same day as other volunteer who
            # cannot work alone
            model.Add(sum(schedule[(id, d, s)] for s in shifts) and
                sum(schedule[(v, d, s)]
                for v in other_not_alones for s in shifts) == False)

    # Does not want to work with XY
    for not_want in not_with_them:
        them = not_want[1]
        days = [d for d in all_days_available[not_want[0]]]
        for d in days:
            model.Add(sum(schedule[(not_want[0], d, s)] for s in shifts)
                and sum(schedule[(v, d, s)]
                for v in them for s in shifts) == False)


    # OBJECTIVE

    # Filled phone shifts has the greatest priority
    model.Maximize(sum(2 * schedule[(v, d, 0)] + schedule[(v, d, 1)]
        + schedule[(v, d, 2)]
        for d in list_of_days for v in volunteers))


    # SOLUTION

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.Solve(model)


    def horizontal_line():
        print('_' * 108)

    first_shift = ''
    print()
    print()
    print(str(schedule_year) + ' ' + month_name)
    for i in range(firstday):
        first_shift = ' ' * 14 * i
    for week in weeks:
        horizontal_line()
        line_0 = ''
        line_1 = ''
        line_2 = ''
        line_3 = ''
        if first_shift:
            line_0 += first_shift
            line_1 += first_shift
            line_2 += first_shift
            line_3 += first_shift
            first_shift = 0

        for d in week:
            phone, chat, observer = False, False, False
            line_0 += '{:<2}'.format(d) + ' ' * 14

            # Phone
            for v in volunteers:
                if solver.Value(schedule[(v, d, 0)]) == 1:
                    phone = True
                    break
            if phone:
                line_1 += 'P: {:<10}'.format(volunteer_dic[v]) + ' ' * 3
            else:
                line_1 += 'P: -' + ' ' * 12

            # Chat
            for v in volunteers:
                if solver.Value(schedule[(v, d, 1)]) == 1:
                    chat = True
                    break
            if chat:
                line_2 += 'C: {:<10}'.format(volunteer_dic[v]) + ' ' * 3
            elif d in chat_days:
                line_2 += 'C: -' + ' ' * 12
            else:
                line_2 += ' ' * 16

            # Observer
            for v in volunteers:
                if solver.Value(schedule[(v, d, 2)]) == 1:
                    observer = True
                    break
            if observer:
                line_3 += 'O: {:<10}'.format(volunteer_dic[v]) + ' ' * 3
            else:
                line_3 += ' ' * 16
        print(line_0)
        print(line_1)
        print(line_2)
        print(line_3)
    horizontal_line()
    print()
    print()
    print()


    # print(str(schedule_year) + ' ' + month_name)
    print('Day|      Phone       Chat    Observer')
    print('___|' + '_' * 38)

    def write_out(value, size, string):
        print('{:>{}}'.format(value, size) + string, end='')

    for d in list_of_days:
        phone, chat, observer = False, False, False
        write_out(d, 2, '.| ')

        # Phone
        for v in volunteers:
            if solver.Value(schedule[(v, d, 0)]) == 1:
                phone = True
                break
        if phone:
            write_out(volunteer_dic[v], 10, ' ')
        else:
            print('      _    ', end='')

        # Chat
        for v in volunteers:
            if solver.Value(schedule[(v, d, 1)]) == 1:
                chat = True
                break
        if chat:
            write_out(volunteer_dic[v], 10, ' ')
        elif d in chat_days:
            print('      _    ', end='')
        else:
            print(' ' * 11, end='')

        # Observer
        for v in volunteers:
            if solver.Value(schedule[(v, d, 2)]) == 1:
                observer = True
                break
        if observer:
            write_out(volunteer_dic[v], 10, ' ')
        print()
    print()


    # print(str(schedule_year) + ' ' + month_name)
    print()
    for v in volunteers:
        has = False
        for d in list_of_days:
            for s in shifts:
                if solver.Value(schedule[(v, d, s)]) == 1:
                    if s == 0:
                        t = 'phone'
                    elif s == 1:
                        t = 'chat'
                    elif s == 2:
                        t = 'observer'
                    if has:
                        print(' ' * 12 + '{:>2}. {}'.format(d,t))
                    else:
                        print('{:>10}: '.format(volunteer_dic[v])
                            + '{:>2}. {}'.format(d,t))
                    has = True
        if has:
            print()
    print()


    # Who works less than willing?
    print('Workloads: ')
    nonzero_capacity = False
    for v in volunteers:
        works = 0
        more = 0
        workload = all_workload[v]
        for d in list_of_days:
            for s in shifts:
                if solver.Value(schedule[(v, d, s)]) == 1:
                    works += 1
        more = workload - works
        if more > 0 or more < 0:
            name = volunteer_dic[v]
            nonzero_capacity = True
            print('{:>10} works {} day'.format(name, works), end='')
            if works > 1:
                print('s', end='')
            print(' but offered', workload, 'day', end='')
            if workload > 1:
                print('s', end='')
            print('.')
    if not nonzero_capacity:
        print('Workloads match originally offered capacity.')
    print()


if __name__ == '__main__':
    main()
