import requests
import datetime
import telegram
from time import sleep

import logging
import telegram
from telegram.error import NetworkError, Unauthorized
from time import sleep
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


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
    print('MARADONA')
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

    return '001', 'Your travel identifier is ' + str(id_travel) + '.', j


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
        return new_travel(info['message']['chat']['username'], info['message']['text'],
                          info['message']['chat']['id'])

    travel = get_travel(travel_id)
    if travel == 'error':
        return '400', 'An error has ocurred. Please start a new travel from the beggining', travel

    if travel['next_step'] == 'set_destination':
        travel['destination'] = info['message']['text']
        return '001', 'Done! Select an option:', travel

    elif travel['next_step'] == 'set_departure_date':
        departure_date = info['message']['text'].split('-')

        if len(departure_date) != 3 or len(departure_date[0]) != 4 or len(departure_date[1]) != 2 or len(departure_date[2]) != 2:
            return '400', 'Incorrect format. Correct format is [yyyy-mm-dd]. Select an option:', travel

        try:
            date = datetime.datetime(int(departure_date[0]), int(departure_date[1]), int(departure_date[2]))
        except:
            return '400', "This date doesn't exists. Select an option:", travel

        now = datetime.datetime.now()
        if date < now:
            return '400', "Depart date can't be a past date. Select an option:", travel

        travel['departure_date'] = info['message']['text']
        return '001', 'Done! Select an option:', travel

    elif travel['next_step'] == 'set_return_date':
        departure_date = travel['departure_date'].split('-')
        return_date = info['message']['text'].split('-')

        if len(return_date) != 3 or len(return_date[0]) != 4 or len(return_date[1]) != 2 or len(return_date[2]) != 2:
            return '400', 'Incorrect format. Correct format is [yyyy-mm-dd]. Select an option:', travel

        try:
            ret_date = datetime.datetime(int(return_date[0]), int(return_date[1]), int(return_date[2]))
            dep_date = datetime.datetime(int(departure_date[0]), int(departure_date[1]), int(departure_date[2]))
        except:
            return '400', "This date doesn't exists. Select an option:", travel

        if ret_date < dep_date:
            return '400', 'Return date must be later than Departure date. Select an option:', travel

        travel['return_date'] = info['message']['text']
        return '001', 'Done! Select an option:', travel

    elif travel['next_step'] == 'member_name':
        member = {'name': info['message']['text']}
        if not 'members' in travel:
            travel['members'] = [member]
        else:
            travel['members'].append(member)

        travel['next_step'] = 'member_origin'

        return '005', 'Insert {} origin city'.format(info['message']['text']), travel

    elif travel['next_step'] == 'member_origin':
        for member in travel['members']:
            if 'origin' not in member:
                member['origin'] = info['message']['text']
                break

        travel['next_step'] = 'enter_members'
        print(database_travel)
        return '001', 'New member created. Select an option:', travel


def new_member(info):
    travel_id = get_id_travel(info.callback_query.message.chat.id)
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
        keyboard = None

        if update.message:
            if update.message.text == '/hello':
                output = 'Hello, wellcome to Group Travel Bot powered by SkyScanner.'
                keyboard = [[InlineKeyboardButton("New travel", callback_data='new_travel'),
                             InlineKeyboardButton("My travels", callback_data='my_travels')],]

            elif update.message.text == '/new_member':
                output = new_member(update)

            else:
                code, output, travel = save_info(update)
                if code in ['001', '400']:
                    if not ('destination' in travel and 'departure_date' in travel and 'return_date' in travel):
                        keyboard = [[InlineKeyboardButton("Set Destination", callback_data='set_destination'),
                                     InlineKeyboardButton("Set Departure date", callback_data='set_departure_date')], ]
                        if 'departure_date' in travel:
                            keyboard = [[InlineKeyboardButton("Set Destination", callback_data='set_destination'),
                                         InlineKeyboardButton("Set Departure date", callback_data='set_departure_date'),
                                         InlineKeyboardButton("Set Return date", callback_data='set_return_date')], ]
                    else:
                        keyboard = [[InlineKeyboardButton("Add Member", callback_data='add_member'),
                                     InlineKeyboardButton("Calculate Results", callback_data='calculate_results'),
                                     InlineKeyboardButton("Edit info", callback_data='edit_info'),
                                     InlineKeyboardButton("Check info", callback_data='check_info')], ]

        elif update.callback_query:
            if update.callback_query.data == 'new_travel':
                output = 'Ok. Insert a name for this travel'

            elif update.callback_query.data == 'set_destination':
                output = 'Ok. Insert the Destination'
                travel = get_travel(get_id_travel(update.callback_query.message.chat.id))
                travel['next_step'] = 'set_destination'

            elif update.callback_query.data == 'set_departure_date':
                output = 'Ok. Enter the Departure date [yyyy-mm-dd]'
                travel = get_travel(get_id_travel(update.callback_query.message.chat.id))
                travel['next_step'] = 'set_departure_date'

            elif update.callback_query.data == 'set_return_date':
                output = 'Ok. Enter the Return date [yyyy-mm-dd]'
                travel = get_travel(get_id_travel(update.callback_query.message.chat.id))
                travel['next_step'] = 'set_return_date'

            elif update.callback_query.data == 'add_member':
                output = new_member(update)

            elif update.callback_query.data == 'edit_info':
                output = 'Select an option: '
                keyboard = [[InlineKeyboardButton("Set Destination", callback_data='set_destination'),
                             InlineKeyboardButton("Set Departure date", callback_data='set_departure_date'),
                             InlineKeyboardButton("Set Return date", callback_data='set_return_date')], ]

            elif update.callback_query.data == 'check_info':
                travel = get_travel(get_id_travel(update.callback_query.message.chat.id))
                output = '*Travel:* ' + str(travel['id']) + '\n*Destination:* ' + str(travel['destination']) + '\n*Departure date:* ' \
                        + str(travel['departure_date']) + '\n*Return date:* ' + str(travel['return_date'])
                if 'members' in travel:
                    output  =+ '\n\n*Members:*'
                    for member in travel['members']:
                        output += '\n' +str(member['name']) + ' travels from ' + str(member['origin'])


        else:
            output = 'ERROR MARADONA'


        if update.message:
            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
                print(output)
                update.message.reply_text(output, reply_markup=reply_markup)
            else:
                update.message.reply_text(output)
        else:
            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.callback_query.message.reply_text(output, reply_markup=reply_markup)
            else:
                update.callback_query.message.reply_text(output)


if __name__ == '__main__':
    main()
