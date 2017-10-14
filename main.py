import requests
import datetime
import telegram
from time import sleep

import logging
import telegram
from telegram.error import NetworkError, Unauthorized
from time import sleep


url = "https://api.telegram.org/bot474902974:AAF_B8om-NzaZNXFqAFcd7ERTFsuDp52THI/"
database_travel = []
ids_map = {}


def get_updates_json(request):
    params = {'timeout': 0, 'offset': None}
    response = requests.get(request + 'getUpdates', data=params)
    return response.json()


def last_update(data):
    results = data['result']
    total_updates = len(results) - 1
    return results[total_updates]



def new_travel(username, name, id_chat):
    id_travel = username + '_' + name
    if id_travel not in ids_map:
        ids_map[id_travel] = [id_chat, ]
    else:
        return 'You have already planned a travel with these name, try a new one please.'

    j = {
        'id': id_travel,
        'next_step': 'destination'
    }
    database_travel.append(j)

    return 'Your travel identifier is ' + str(id_travel) + '.\n Which will be your destination?'


def get_id_travel(chat_id):
    for key, values in ids_map.items():
        if chat_id in values:
            return key

    return 'error'


def get_travel(travel_id):
    for res in database_travel:
        print(res)
        if res['id'] == travel_id:
            return res

    return 'error'


def save_info(info):
    travel_id = get_id_travel(info['message']['chat']['id'])
    if travel_id == 'error':
        return 'An error has ocurred. Please start a new travel from the beggining'

    travel = get_travel(travel_id)
    if travel == 'error':
        return 'An error has ocurred. Please start a new travel from the beggining'

    if travel['next_step'] == 'destination':
        travel['destination'] = info['message']['text']
        travel['next_step'] = 'depart_date'
        return 'Enter the Departure date [yyyy-mm-dd]'

    elif travel['next_step'] == 'depart_date':
        depart_date = info['message']['text'].split('-')

        if len(depart_date) != 3 or len(depart_date[0]) != 4 or len(depart_date[1]) != 2 or len(depart_date[2]) != 2:
            return 'Incorrect format. Please enter the Departure date [yyyy-mm-dd]'

        try:
            date = datetime.datetime(int(depart_date[0]), int(depart_date[1]), int(depart_date[2]))
        except:
            return "This date doesn't exists"

        now = datetime.datetime.now()
        if date < now:
            return "Depart date can't be a past date"

        travel['depart_date'] = info['message']['text']
        travel['next_step'] = 'return_date'
        return 'Enter the Return date [yyyy-mm-dd]'

    elif travel['next_step'] == 'return_date':
        departure_date = travel['depart_date'].split('-')
        return_date = info['message']['text'].split('-')

        if len(return_date) != 3 or len(return_date[0]) != 4 or len(return_date[1]) != 2 or len(return_date[2]) != 2:
            return 'Incorrect format. Please enter the Return date [yyyy-mm-dd]'

        try:
            ret_date = datetime.datetime(int(return_date[0]), int(return_date[1]), int(return_date[2]))
            dep_date = datetime.datetime(int(departure_date[0]), int(departure_date[1]), int(departure_date[2]))
        except:
            return "This date doesn't exists"

        if ret_date < dep_date:
            return 'Return date must be later than Departure date. Enter the Return date [yyyy-mm-dd]'

        travel['return_date'] = info['message']['text']
        travel['next_step'] = 'enter_members'
        return 'Create a new member by using the command /new_member'

    elif travel['next_step'] == 'member_name':
        member = {'name': info['message']['text']}
        if not 'members' in travel:
            travel['members'] = [member]
        else:
            travel['members'].append(member)

        travel['next_step'] = 'member_origin'

        return 'Insert {} origin city'.format(info['message']['text'])

    elif travel['next_step'] == 'member_origin':
        for member in travel['members']:
            if 'origin' not in member:
                member['origin'] = info['message']['text']
                break

        travel['next_step'] = 'enter_members'

        return 'New member created. Create a new member by using the command /new_member'


def new_member(info):
    travel_id = get_id_travel(info['message']['chat']['id'])
    if travel_id == 'error':
        return 'An error has ocurred. Please start a new travel from the beggining'

    travel = get_travel(travel_id)
    if travel == 'error':
        return 'An error has ocurred. Please start a new travel from the beggining'

    travel['next_step'] = 'member_name'
    return "Insert member's name"


update_id = None

def main():
    global update_id
    # Telegram Bot Authorization Token
    bot = telegram.Bot('474902974:AAF_B8om-NzaZNXFqAFcd7ERTFsuDp52THI')

    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    try:
        '''update_id = bot.get_updates()[0].update_id'''
        update_id = last_update(get_updates_json(url))['update_id']
    except IndexError:
        update_id = None

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    while True:
        try:
            engine(bot)
        except NetworkError:
            sleep(1)
        except Unauthorized:
            # The user has removed or blocked the bot.
            update_id += 1


def engine(bot):
    global update_id
    # Request updates after the last update_id

    last_input = last_update(get_updates_json(url))
    if update_id == last_input['update_id']:
        update = bot.get_updates(offset=update_id, timeout=10)[0]
        update_id += 1

        if update.message.text == '/hello':
            output = 'Hello, wellcome to Group Travel Bot powered by SkyScanner. To start planning a new travel write /new_travel'


        elif update.message.text.split(' ')[0] == '/new_travel':
            output = new_travel(update.message.chat.username, update.message.text.split(' ')[1],
                                update.message.chat.id)


        elif update.message.text == '/new_member':
            output = new_member(update)

        else:
            output = save_info(update)

        update.message.reply_text(output)


if __name__ == '__main__':
    main()
