from collections import defaultdict
from operator import itemgetter

from Tools import Tools
from Sessions import Sessions
from Competitions import DATABASE
from Competitions import Competitions
from Entrys import Entrys
from Styles import Style


"""
https://stackoverflow.com/questions/1210458/how-can-i-generate-a-unique-id-in-python
"""
import threading
_uid = threading.local()
def gen_uid():
    if getattr(_uid, "uid", None) is None:
        _uid.tid = threading.current_thread().ident
        _uid.uid = 0
    _uid.uid += 1
    return (_uid.tid, _uid.uid)

# create logger
import logging
import os



LEVEL = logging.INFO
logger = logging.getLogger(os.path.basename(__file__).split('.')[0] if __name__ == '__main__' else __name__.split('.')[0])

logger.setLevel(LEVEL)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(LEVEL)

# create formatter
formatter = logging.Formatter('%(asctime)s.%(msecs)03d: %(levelname)s: %(name)s.%(funcName)s(): %(message)s', datefmt='%m-%d-%Y %H:%M:%S')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
# end create logger


logging.captureWarnings(True)  #eliminate the insecure warnings on the console


from MySql import local_host
from Database import Database
from Database import escape_sql

db = Database(local_host['host'], local_host['user'], local_host['password'], DATABASE)


class Flights:

    def __init__(self):

        pass


    def auto_assign_judges(self, session_number):

        BJCP_MULTIPLIER = 2  #because BJCP judges are just better ;-)

        result = self.get_judges_for_session(session_number)
        ranks = Tools().get_cert_rank()

        #calculate ranking for all judges in session
        for r in result:

            r['rank'] = 0

            if r['bjcp_rank']:
                r['rank'] += ranks['BJCP'][r['bjcp_rank']] * BJCP_MULTIPLIER

            if r['cicerone']:
                r['rank'] += ranks['Cicerone'][r['cicerone']]

            if r['other_cert']:
                r['rank'] += ranks['Other'][r['other_cert']]

            r['rank'] += r['ncbc_points'] if r['ncbc_points'] else 0

        #get reverse ordered list of judges by the ranking
        judges = [x for x in sorted(result, key=lambda k: k['rank'], reverse=True)]

        for i in judges:
            print(i['firstname'], i['dislikes'])

        # split the judges in half
        half = len(judges) // 2
        head_judges = judges[:half]
        judges = judges[half:]

        pairing = []

        while head_judges:

            #get head judge pkid and don't pair list
            hj = head_judges.pop()
            hj_pkid = str(hj['pkid'])
            hj_dont_pair = hj['dont_pair'].split(',') if hj['dont_pair'] else []

            #postion of match in judges list
            position = 0

            for judge in judges:
                #get judges don't pair list
                j_dont_pair = judge['dont_pair'].split(',') if judge['dont_pair'] else []

                #if head judge pkid not in judge do not pair with and
                #judge pkid not in head judge do not pair with then pair the judges
                if hj_pkid not in j_dont_pair and str(judge['pkid']) not in hj_dont_pair:
                    print('pairing judge:', judge)
                    pairing.append([hj, judge])
                    break

                #otherwise go to the next position in the judges list
                position += 1

            #if position count is = len of judges list then didn't match head judge, add to the list without judging mate
            if position >= len(judges):
                pairing.append([hj, {}])

            #if matched then remove the judge from the list
            else:
                judges.pop(position)


        return {'pairing': pairing, 'judges': judges}


    def get_judges_for_session(self, session_number):
        print('session_number', session_number)
        result = Sessions().get_session_volunteers(session_number, judges=True)
        print('judges')

        for r in result:
            print(r)

        session_list = Sessions().get_daily_pkids(session_number)
        print('session list', session_list)

        for r in result:

            count = 0
            judge_sessions = r['fk_sessions_list'].split(',')

            for s in session_list:

                count += judge_sessions.count(str(s))

            r['total_day'] = count
            r['total_sessions'] = len(judge_sessions)

        return result


    def get_session_pairing(self, session_number):

        sql = 'select * from judge_pairing where fk_sessions = "{}" ' \
              ''.format(session_number)
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result


    def get_flights(self):

        sql = 'select * from flights where fk_competitions = "{}"'.format(Competitions().get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result



def complete_flight():

    flights = Flights().get_flights()

    flight_numbers = set([x['number'] for x in flights])

    #print(flight_numbers)
    #print(flights[0])

    try:
        choice = input('Enter flight number to process: ')
    except Exception as e:
        choice = ''
    
    try:
        choice = int(choice)
    except:
        choice = ''

    if choice == '':
        return

    print(f'Found flight {choice in flight_numbers}')

    my_flight = '{:02d}'.format(choice)
    print(f'Entry IDs for flight {my_flight}')

    entries = Entrys().get_inventory(inventory=True)

    cat_entries = {}

    for entry in entries:
        entry_flight = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')

        if entry_flight == my_flight and entry['judged'] == 0:
            cat_entries[entry['entry_id']] = entry
    
    if not cat_entries:
        print('Found no entry IDs')
        return

    print(list(cat_entries.keys()))

    place = {}
    
    for i in range(1, 5):

        get_input = True

        while get_input:

            try:
                choice = input(f'Place {i}: ')
            except Exception as e:
                choice = ''

            try:
                choice = int(choice)
            except:
                choice = ''

            if choice in cat_entries or choice == '':
                place[i] = choice
                get_input = False
    print(place)

    try:
        choice = input('Is this correct (y/n) ')
    except Exception as e:
        choice = ''

    choice = choice.lower()

    if choice == 'y':
        print('Saving flight places')

        sql_entry_ids = '","'.join([str(x) for x in cat_entries.keys()])
        sql = (f'update entries set judged="1" where fk_competitions = "{Competitions().get_active_competition()}" '
                f'and entry_id in ("{sql_entry_ids}")'
              )
        db.db_command(sql=sql)

        for p in place:
            if place[p]:
                sql = (f'update entries set place="{p}" where fk_competitions = "{Competitions().get_active_competition()}" '
                        f'and entry_id = "{place[p]}"'
                    )
                db.db_command(sql=sql)



def enter_overall_winners():

    sql = 'select * from entries where fk_competitions="5" and place="1"'
    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).all(uid)

    entry_ids = [x['entry_id'] for x in result]
    print(entry_ids)

    place = {}
    
    for i in range(1, 5):

        get_input = True

        while get_input:

            try:
                choice = input(f'Place {i}: ')
            except Exception as e:
                choice = ''

            try:
                choice = int(choice)
            except:
                choice = ''

            if choice in entry_ids or choice == '':
                place[i] = choice
                get_input = False
    print(place)

    try:
        choice = input('Is this correct (y/n) ')
    except Exception as e:
        choice = ''

    choice = choice.lower()

    if choice == 'y':

        for p in place:
            if place[p]:
                sql = (f'update entries set bos_place="{p}" where fk_competitions = "{Competitions().get_active_competition()}" '
                        f'and entry_id = "{place[p]}"'
                    )
                db.db_command(sql=sql)




        
def mini_bos_flight():

    flights = Flights().get_flights()

    flight_numbers = set([x['number'] for x in flights])

    #print(flight_numbers)
    #print(flights[0])

    try:
        choice = input('Enter mini-BOS flight number to process: ')
    except Exception as e:
        choice = ''
    
    try:
        choice = int(choice)
    except:
        choice = ''

    if choice == '':
        return

    print(f'Found flight {choice in flight_numbers}')

    my_flight = '{:02d}'.format(choice)
    print(f'Entry IDs for flight {my_flight}')

    entries = Entrys().get_inventory(inventory=True)

    cat_entries = {}

    for entry in entries:
        entry_flight = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')

        if entry_flight == my_flight and entry['judged'] == 0:
            cat_entries[entry['entry_id']] = entry
    
    if not cat_entries:
        print('Found no entry IDs')
        return
    print(list(cat_entries.keys()))

    mini_bos = []
    choice = True
    while choice:

        choice = ''

        get_input = True

        while get_input:

            try:
                choice = input(f'mini-BOS: ')
            except Exception as e:

                choice = ''

            try:
                choice = int(choice)
            except:
                choice = ''

            if choice in cat_entries:
                mini_bos.append(choice)
            if choice == '':
                get_input = False
    print(mini_bos)

    try:
        choice = input('Is this correct (y/n) ')
    except Exception as e:
        choice = ''

    choice = choice.lower()
    
    if choice == 'y':
        print('Saving Mini-BOS entries')

        sql_entry_ids = '","'.join([str(x) for x in mini_bos])
        sql = (f'update entries set mini_bos="1" where fk_competitions = "{Competitions().get_active_competition()}" '
                f'and entry_id in ("{sql_entry_ids}")'
              )
        #print(sql)
        db.db_command(sql=sql)


def get_completed_flights():

    # Todo: get from db
    locations = {
        1: 'RTP',
        3: 'AVL'
    }

    flights = Flights().get_flights()
    entries = Entrys().get_inventory(inventory=True)

    judged_flights = {}

    for entry in entries:
        entry_flight = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')

        fk_judge_locations = [x for x in flights if x['number'] == int(entry_flight)]

        if entry['judged'] == 1:

            if entry_flight not in judged_flights:
                judged_flights[entry_flight] = {
                    1: '',
                    2: '',
                    3: '',
                    4: '',
                    'pulled_bos': 'No',
                    'loc': locations[fk_judge_locations[0]['fk_judge_locations']] if fk_judge_locations else ''
                }

            place = entry['place']

            if place:
                judged_flights[entry_flight][place] = entry['entry_id']

                if place == 1:
                    judged_flights[entry_flight]['pulled_bos'] = 'Yes' if entry['pulled_bos'] == 1 else 'No'

    for flight in sorted(judged_flights):

        print(f'{flight} {judged_flights[flight]}')
    print(f'Number of completed flights: {len(judged_flights)}')


def get_completed_flights_avl_only():

    # Todo: get from db
    locations = {
        1: 'RTP',
        3: 'AVL'
    }

    flights = Flights().get_flights()
    entries = Entrys().get_inventory(inventory=True)

    judged_flights = {}

    for entry in entries:
        entry_flight = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')

        fk_judge_locations = [x for x in flights if x['number'] == int(entry_flight)]

        if entry['judged'] == 1:

            if entry_flight not in judged_flights:
                judged_flights[entry_flight] = {
                    1: '',
                    2: '',
                    3: '',
                    4: '',
                    'pulled_bos': 'No',
                    'loc': locations[fk_judge_locations[0]['fk_judge_locations']] if fk_judge_locations else ''
                }

            place = entry['place']

            if place:
                judged_flights[entry_flight][place] = entry['entry_id']

                if place == 1:
                    judged_flights[entry_flight]['pulled_bos'] = 'Yes' if entry['pulled_bos'] == 1 else 'No'

    flt_count = 0
    for flight in sorted(judged_flights):
        
        # Todo: only interested in AVL beers this year
        if judged_flights[flight]['loc'] == 'AVL':
            flt_count += 1
            print(f'{flight} {judged_flights[flight]}')
    print(f'Number of completed flights: {flt_count}')

    
def get_completed_flights_rtp_only():

    # Todo: get from db
    locations = {
        1: 'RTP',
        3: 'AVL'
    }

    flights = Flights().get_flights()
    entries = Entrys().get_inventory(inventory=True)

    judged_flights = {}

    for entry in entries:
        entry_flight = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')

        fk_judge_locations = [x for x in flights if x['number'] == int(entry_flight)]

        if entry['judged'] == 1:

            if entry_flight not in judged_flights:
                judged_flights[entry_flight] = {
                    1: '',
                    2: '',
                    3: '',
                    4: '',
                    'pulled_bos': 'No',
                    'loc': locations[fk_judge_locations[0]['fk_judge_locations']] if fk_judge_locations else ''
                }

            place = entry['place']

            if place:
                judged_flights[entry_flight][place] = entry['entry_id']

                if place == 1:
                    judged_flights[entry_flight]['pulled_bos'] = 'Yes' if entry['pulled_bos'] == 1 else 'No'

    flt_count = 0
    for flight in sorted(judged_flights):
        
        # Todo: only interested in AVL beers this year
        if judged_flights[flight]['loc'] == 'RTP':
            flt_count += 1
            print(f'{flight} {judged_flights[flight]}')
    print(f'Number of completed flights: {flt_count}')

    

def mark_bos_pulled():

    # todo: make finction more generic

    sql = 'select entry_id from entries where place = "1" and pulled_bos = "0" and fk_competitions = "5"'

    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).all(uid)

    entry_ids = [x['entry_id'] for x in result]
    print(entry_ids)

    try:
        entry_id = input('Enter BOS Entry ID Pulled: ')
    except Exception as e:
        entry_id = ''
    
    try:
        entry_id = int(entry_id)
    except:
        entry_id = ''

    if entry_id == '':
        return

    found_entry = entry_id in entry_ids
    print(f'Found entry {entry_id} - {found_entry}')

    if found_entry:

        try:
            choice = input(f'BOS Entry {entry_id} has been pulled (y/n) ')
        except Exception as e:
            choice = ''

        choice = choice.lower()
        
        if choice == 'y':
            print(f'Setting {entry_id} as found')

            sql = (f'update entries set pulled_bos="1" where fk_competitions = "{Competitions().get_active_competition()}" '
                    f'and entry_id = "{entry_id}"'
                )
            #print(sql)
            db.db_command(sql=sql)


def winner_report():


    flights = Flights().get_flights()
    entries = Entrys().get_inventory(inventory=True, place=True)

    sql = 'select * from entries where fk_competitions="5" and bos_place<>"0"'
    uid = gen_uid()
    bos = db.db_command(sql=sql, uid=uid).all(uid)

    winners = []

    if bos:
        print('\nNCBC 2021 Best Of Show')
    for entry in bos:

        flight_number = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')
        flight_name = Style('NCBC2020').get_category_name(flight_number)
        style_name = Style('NCBC2020').get_style_name(entry["category"], entry["sub_category"])
        brewer = Entrys().get_brewer(entry['fk_brewers'])

        winners.append([f'"{flight_name}"',
                                                        f'"{entry["category"]}{entry["sub_category"]} {style_name}"',
                                                        f'BOS {entry["bos_place"]}',
                                                        f'"{brewer["organization"]}"',
                                                        f'"{entry["name"]}"',
        ])
        
        
    
    for entry in sorted(winners, key = lambda x: x[2]):
        print(','.join(entry))

    print('\nNCBC 2021 Category Winners')

    winners = defaultdict(list)

    for entry in entries:
        flight_number = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')
        flight_name = Style('NCBC2020').get_category_name(flight_number)
        style_name = Style('NCBC2020').get_style_name(entry["category"], entry["sub_category"])
        brewer = Entrys().get_brewer(entry['fk_brewers'])

        winners[f'{flight_number} {flight_name}'].append([f'"{flight_name}"',
                                                        f'"{entry["category"]}{entry["sub_category"]} {style_name}"',
                                                        f'{entry["place"]}',
                                                        f'"{brewer["organization"]}"',
                                                        f'"{entry["name"]}"'
        ])
        
        
    
    for cat in sorted(winners):
        for entry in sorted(winners[cat], key = lambda x: int(x[2])):
            print(','.join(entry))

def orgainzers_pull_list():


    flights = Flights().get_flights()
    winners_entries = Entrys().get_inventory(inventory=True, place=True)
    entries = Entrys().get_inventory(inventory=True, place=False)

        
    with open(f'public/reports/Orgainzers pull list.csv', 'w') as f:

        winners = defaultdict(list)

        for entry in winners_entries:
            flight_number = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')
            flight_name = Style('NCBC2020').get_category_name(flight_number)
            style_name = Style('NCBC2020').get_style_name(entry["category"], entry["sub_category"])
            brewer = Entrys().get_brewer(entry['fk_brewers'])

            winners[f'{flight_number} {flight_name}'].append(['    ',
                                                            f'{entry["place"]}',
                                                            f'"{entry["entry_id"]}"',
                                                            f'"{entry["category"]}{entry["sub_category"]} {style_name}"',
                                                            f'"{brewer["organization"]}"',
                                                            f'"{entry["name"]}"'
            ])
            
        for entry in entries:
            flight_number = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')
            flight_name = Style('NCBC2020').get_category_name(flight_number)
            style_name = Style('NCBC2020').get_style_name(entry["category"], entry["sub_category"])
            brewer = Entrys().get_brewer(entry['fk_brewers'])

            winners[f'{flight_number} {flight_name}'].append(['    ',
                                                            f'',
                                                            f'"{entry["entry_id"]}"',
                                                            f'"{entry["category"]}{entry["sub_category"]} {style_name}"',
                                                            f'"{brewer["organization"]}"',
                                                            f'"{entry["name"]}"'
            ])        
        
        for cat in sorted(winners):
            f.write(f'{cat}\n')
            for entry in sorted(winners[cat], key = lambda x: x[1] if x[1] else f'z{x[2]}'):
                f.write(f"{','.join(entry)}\n")

def orgainzers_pull_list_by_brewery():


    flights = Flights().get_flights()
    entries = Entrys().get_inventory(inventory=True,)

    brewers = defaultdict(list)
    
    with open(f'public/reports/Brewers pull list.csv', 'w') as f:


            
        for entry in entries:
            flight_number = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')
            flight_name = Style('NCBC2020').get_category_name(flight_number)
            style_name = Style('NCBC2020').get_style_name(entry["category"], entry["sub_category"])
            brewer = Entrys().get_brewer(entry['fk_brewers'])

            place = str(entry["place"])
            brewers[f'{brewer["organization"]}'].append(['    ',
                                                            f'' if place == '0' else place,
                                                            f'"{entry["entry_id"]}"',
                                                            f'"{flight_number}"',
                                                            f'"{entry["category"]}{entry["sub_category"]} {style_name}"',
                                                            f'"{brewer["organization"]}"',
                                                            f'"{entry["name"]}"'
            ])        
        
        for brewer in sorted(brewers):
            print(brewer)
            f.write(f'{brewer}\n')
            for entry in sorted(brewers[brewer], key = lambda x: x[1] if x[1] else f'z{x[2]}'):
                f.write(f"{','.join(entry)}\n")




def winner_report_with_entry_id():


    flights = Flights().get_flights()
    entries = Entrys().get_inventory(inventory=True, place=True)

    sql = 'select * from entries where fk_competitions="6" and bos_place<>"0"'
    uid = gen_uid()
    bos = db.db_command(sql=sql, uid=uid).all(uid)

    winners = []

    if bos:
        print('\nNCBC 2021 Best Of Show')
    for entry in bos:

        flight_number = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')
        flight_name = Style('NCBC2020').get_category_name(flight_number)
        style_name = Style('NCBC2020').get_style_name(entry["category"], entry["sub_category"])
        brewer = Entrys().get_brewer(entry['fk_brewers'])

        winners.append(['    ',
                                                        f'"{entry["entry_id"]}"',
                                                        f'"{flight_name}"',
                                                        f'"{entry["category"]}{entry["sub_category"]} {style_name}"',
                                                        f'BOS {entry["bos_place"]}',
                                                        f'"{brewer["organization"]}"',
                                                        f'"{entry["name"]}"',
        ])
        
        
    
    for entry in sorted(winners, key = lambda x: x[4]):
        print(','.join(entry))

    print('\nNCBC 2021 Category Winners')

    winners = defaultdict(list)

    for entry in entries:
        flight_number = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')
        flight_name = Style('NCBC2020').get_category_name(flight_number)
        style_name = Style('NCBC2020').get_style_name(entry["category"], entry["sub_category"])
        brewer = Entrys().get_brewer(entry['fk_brewers'])

        winners[f'{flight_number} {flight_name}'].append(['    ',
                                                        f'"{entry["entry_id"]}"',
                                                        f'"{flight_name}"',
                                                        f'"{entry["category"]}{entry["sub_category"]} {style_name}"',
                                                        f'{entry["place"]}',
                                                        f'"{brewer["organization"]}"',
                                                        f'"{entry["name"]}"'
        ])
        
        
    
    for cat in sorted(winners):
        print(cat)
        for entry in sorted(winners[cat], key = lambda x: int(x[4])):
            print(','.join(entry))



def place_pull_sheet():


    flights = Flights().get_flights()
    entries = Entrys().get_inventory(inventory=True, place=True)

    winners = defaultdict(list)

    for entry in entries:
        flight_number = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')
        flight_name = Style('NCBC2020').get_category_name(flight_number)
        style_name = Style('NCBC2020').get_style_name(entry["category"], entry["sub_category"])
        brewer = Entrys().get_brewer(entry['fk_brewers'])

        winners[f'{flight_number} {flight_name}'].append(['', f'{entry["entry_id"]}',
                                                        f'"{entry["category"]}{entry["sub_category"]} {style_name}"',
                                                        f'{entry["place"]}',
                                                        f'"{brewer["organization"]}"',
                                                        f'"{entry["name"]}"'
        ])
        
        
    
    for cat in sorted(winners):
        print(cat)
        for entry in sorted(winners[cat], key = lambda x: int(x[3])):
            print(','.join(entry))


def all_pull_sheet():


    flights = Flights().get_flights()
    entries = Entrys().get_inventory(inventory=True)

    winners = defaultdict(list)

    for entry in entries:
        flight_number = Style('NCBC2020').get_judging_category(f'{entry["category"]}{entry["sub_category"]}')
        flight_name = Style('NCBC2020').get_category_name(flight_number)
        style_name = Style('NCBC2020').get_style_name(entry["category"], entry["sub_category"])
        brewer = Entrys().get_brewer(entry['fk_brewers'])

        winners[f'{flight_number} {flight_name}'].append(['', f'{entry["entry_id"]}',
                                                        f'"{entry["category"]}{entry["sub_category"]} {style_name}"',
                                                        f'{entry["place"]}',
                                                        f'"{brewer["organization"]}"',
                                                        f'"{entry["name"]}"'
        ])
        
        
    
    for cat in sorted(winners):
        print(cat)
        for entry in sorted(winners[cat], key = lambda x: int(x[3])):
            print(','.join(entry))



if __name__ == '__main__':

    #complete_flight()
    #mini_bos_flight()
    #get_completed_flight()
    #mark_bos_pulled()

    winner_report_with_entry_id()
    #orgainzers_pull_list()
    #orgainzers_pull_list_by_brewery()

    #winner_report()
    #place_pull_sheet()
    #all_pull_sheet()

    """
    result = Flights().auto_assign_judges(89)

    for p in result['pairing']:
        print(p)

    print('remaining', result['judges'])
    """



    pass