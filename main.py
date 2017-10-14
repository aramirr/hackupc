import requests
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


def get_chat_id(update):
    chat_id = update['message']['chat']['id']
    return chat_id


def send_mess(chat, text):
    params = {'chat_id': chat, 'text': text}
    response = requests.post(url + 'sendMessage', data=params)
    return response


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

        travel['depart_date'] = info['message']['text']
        travel['next_step'] = 'return_date'
        return 'Enter the Return date [yyyy-mm-dd]'

    elif travel['next_step'] == 'return_date':
        departure_date = travel['depart_date'].split('-')
        return_date = info['message']['text'].split('-')

        if len(return_date) != 3 or len(return_date[0]) != 4 or len(return_date[1]) != 2 or len(return_date[2]) != 2:
            return 'Incorrect format. Please enter the Return date [yyyy-mm-dd]'

        if int(departure_date[0]) > int(return_date[0]) or (int(departure_date[0]) == int(return_date[0]) and int(departure_date[1]) > int(return_date[1]) or (int(departure_date[0]) == int(return_date[0]) and int(departure_date[1]) == int(return_date[1]) and int(departure_date[2]) > int(return_date[2]))):
            return 'Return date must be later than Departure date. Enter the Return date [yyyy-mm-dd]'

        travel['return_date'] = info['message']['text']
        travel['next_step'] = 'enter_members'
        return 'Create new member by using the command /new_member'


def main():
    update_id = last_update(get_updates_json(url))['update_id']
    while True:
        last_input = last_update(get_updates_json(url))
        if update_id == last_input['update_id']:
            print(last_input)
            if last_input['message']['text'] == '/hello':
                output = 'Hello, wellcome to Group Travel Bot powered by SkyScanner. To start planning a new travel write /new_travel'

            elif last_input['message']['text'].split(' ')[0] == '/new_travel':
                output = new_travel(last_input['message']['from']['username'], last_input['message']['text'].split(' ')[1], last_input['message']['chat']['id'])

            else:
                output =save_info(last_input)

            send_mess(last_input['message']['chat']['id'], output)
            update_id += 1

        sleep(1)


if __name__ == '__main__':
    main()