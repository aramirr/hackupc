import requests
import datetime

api_key = 'ha772136595894388989224959580308'

places_api_url = 'http://partners.api.skyscanner.net/apiservices/autosuggest/v1.0/{}/{}/{}'
flights_browse_prices = 'http://partners.api.skyscanner.net/apiservices/browsedates/v1.0/{}/{}/{}/{}/{}/{}/{}'
#http://partners.api.skyscanner.net/apiservices/browsequotes/v1.0/

start_session_url = 'http://partners.api.skyscanner.net/apiservices/pricing/v1.0'


defaults = {'country': 'ES', 'currency': 'eur', 'locale': 'en-us'}

useful_fields_leg = ['Id', 'OriginStation', 'DestinationStation', 'Departure', 'Arrival', 'Stops', 'Carriers', 'Directionality']

class SkyscannerException(Exception):
    def __init__(self, value):
        self.value = value
        self.msg = value
    def __str__(self):
        return repr(self.value)


def get_autocomplete_place_results(query, country=defaults['country'], currency=defaults['currency'], locale=defaults['locale']):
    params = {'apiKey': api_key, 'query': query}
    ret = requests.get(places_api_url.format(country, currency, locale), params=params)
    return ret.json()['Places']


def get_most_similar_id_from_autocomplete_result(query):
    try:
        autocomplete_list = get_autocomplete_place_results(query)
        if len(autocomplete_list) == 0:
            raise SkyscannerException('NoAutocompleteCities ' + query)
        return autocomplete_list[0]['PlaceId']
    except SkyscannerException as e:
        print('Error: ' + e.msg)
        raise e


def i_get_carrier_names(best_quote, request_response, key):
    best_quote[key]['CarrierInfo'] = []
    for carrier_id in best_quote[key]['Carriers']:
        for carrier in request_response['Carriers']:
            if carrier['Id'] == carrier_id:
                best_quote[key]['CarrierInfo'].append(carrier)
                break


def get_carrier_names(best_quote, request_response):
    i_get_carrier_names(best_quote, request_response, 'OutboundLeg')
    i_get_carrier_names(best_quote, request_response, 'InboundLeg')


def add_airports_to_leg(leg, places):
    aux_leg = {key: leg[key] for key in useful_fields_leg}
    for place in places:
        if aux_leg['OriginStation'] == place['Id']:
            if place['Type'] != 'Airport':
                print('not an airport')
            aux_leg['OriginAirportCode'] = place['Code']
            if 'DestinationAirportCode' in aux_leg.keys():
                break
        if aux_leg['DestinationStation'] == place['Id']:
            if place['Type'] != 'Airport':
                print('not an airport')
            aux_leg['DestinationAirportCode'] = place['Code']
            if 'OriginAirportCode' in aux_leg.keys():
                break
    return aux_leg


def get_result_and_build_json(request_response):
    try:
        if len(request_response['Itineraries']) == 0:
            raise SkyscannerException('NoRoundTrip')

        best_result = request_response['Itineraries'][0]

        quote = {}

        i = 0
        for leg in request_response['Legs']:
            if leg['Id'] == best_result['OutboundLegId']:
                quote['OutboundLeg'] = add_airports_to_leg(leg, request_response['Places'])
                i += 1
                if i == 2:
                    break
            if leg['Id'] == best_result['InboundLegId']:
                quote['InboundLeg'] = add_airports_to_leg(leg, request_response['Places'])
                i += 1
                if i == 2:
                    break



        get_carrier_names(quote, request_response)

        quote['MinPrice'] = min(best_result['PricingOptions'], key=lambda price_option: price_option['Price'])['Price']
        quote['link'] = min(best_result['PricingOptions'], key=lambda price_option: price_option['Price'])['DeeplinkUrl']

        return quote
    except Exception as e:
        print('Error: ' + str(e))
        raise e


def start_session(origin_place, destination_place, outbound_partial_date, inbound_partial_date, country=defaults['country'], currency=defaults['currency'], locale=defaults['locale']):
    try:
        origin_place_autocomplete = get_most_similar_id_from_autocomplete_result(origin_place)
        destination_place_autocomplete = get_most_similar_id_from_autocomplete_result(destination_place)

        params = {
            'country': country,
            'currency': currency,
            'locale': locale,
            'originplace': origin_place_autocomplete,
            'destinationplace': destination_place_autocomplete,
            'outbounddate': outbound_partial_date,
            'inbounddate': inbound_partial_date,
            'adults': 1,
            'apikey': api_key
        }
        response = requests.post(start_session_url, data=params)
        current_session_url = response.headers['location']

        return current_session_url

    except SkyscannerException as e:
        print('Error: ' + e.msg)
        raise e


def get_best_quote(request_url):
    params = {
        'apiKey': api_key,
        'sortType': 'price'
    }

    try:
        response = requests.get(request_url, params=params)
        response = response.json()

        if 'ValidationErrors' in response.keys():
            raise SkyscannerException('ValidationErrors_' + response['ValidationErrors']['Message'])
        return get_result_and_build_json(response)
    except SkyscannerException as e:
        if 'ValidationError' in e.value:
            print('Error: ' + e.msg)
        return {'error': e.value}
    except Exception as e:
        print('Error: ' + str(e))
        raise SkyscannerException('ErrorGet')



def generate_request_quotes(api_url, origin_place, destination_place, outbound_partial_date, inbound_partial_date, country=defaults['country'], currency=defaults['currency'], locale=defaults['locale']):
    try:
        origin_place_autocomplete = get_most_similar_id_from_autocomplete_result(origin_place)
        destination_place_autocomplete = get_most_similar_id_from_autocomplete_result(destination_place)

        req = api_url.format(country, currency, locale, origin_place_autocomplete, destination_place_autocomplete, outbound_partial_date,
                                         inbound_partial_date)
        return req
    except Exception as e:
        #print('Error: ' + e.msg)
        raise e


def get_depart_return_date_member(member, input):
    depart_date = member['departure_date'] if 'departure_date' in member.keys() else input['departure_date']
    return_date = member['return_date'] if 'return_date' in member.keys() else input['return_date']
    return depart_date, return_date


def compute_min_flights_for_all(input):
    results = []
    for member in input['members']:
        try:
            depart_date, return_date = get_depart_return_date_member(member, input)
            session_url = start_session(member['origin'], input['destination'], depart_date, return_date)
            aux = get_best_quote(session_url)
            aux['name'] = member['name']
            results.append(aux)
            aux['OutboundLeg']['Departure'] = aux['OutboundLeg']['Departure'].replace('T', ' ')
            aux['OutboundLeg']['Arrival'] = aux['OutboundLeg']['Arrival'].replace('T', ' ')
            aux['InboundLeg']['Departure'] = aux['InboundLeg']['Departure'].replace('T', ' ')
            aux['InboundLeg']['Arrival'] = aux['InboundLeg']['Arrival'].replace('T', ' ')
        except Exception as e:
            results.append({'name': member['name'], 'error': e})
    return results



if __name__ == '__main__':
    input = {'id': 'MrTakis_ny', 'next_step': 'enter_members', 'destination': 'new york', \
            'departure_date': '2017-12-23', 'return_date': '2018-01-11', \
            'members': [{'name': 'Sacrest', 'origin': 'stockholm'}, {'name': 'Mirotic', 'origin': 'rome'}, \
            {'name': 'case', 'origin': 'barcelona'}, {'name': 'oscar', 'origin': 'bologne'}]}

    aux = compute_min_flights_for_all(input)
    print(aux)