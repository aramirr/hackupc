import requests

api_key = 'ha772136595894388989224959580308'

places_api_url = 'http://partners.api.skyscanner.net/apiservices/autosuggest/v1.0/{}/{}/{}'

flights_browse_prices = 'http://partners.api.skyscanner.net/apiservices/browsequotes/v1.0/{}/{}/' \
    '{}/{}/{}/{}/{}'

defaults = {'country': 'ES', 'currency': 'eur', 'locale': 'en-us'}


def get_autocomplete_place_results(query, country=defaults['country'], currency=defaults['currency'], locale=defaults['locale']):
    params = {'apiKey': api_key, 'query': query}
    ret = requests.get(places_api_url.format(country, currency, locale), params=params)
    return ret.json()['Places']


def get_most_similar_id_result_autocomplete(query):
    return get_autocomplete_place_results(query)[0]['PlaceId']


def get_carrier_names(best_quote, request_response):
    key = 'OutboundLeg'
    best_quote[key]['CarrierNames'] = []
    for carrier_id in best_quote[key]['CarrierIds']:
        for carrier in request_response['Carriers']:
            if carrier['CarrierId'] == carrier_id:
                best_quote[key]['CarrierNames'].append(carrier['Name'])
                break


def get_result_and_build_json(request_response):
    request_response['Quotes'] = list(filter(lambda quote: ('OutboundLeg' in quote.keys()) and ('InboundLeg' in quote.keys()), request_response['Quotes']))
    request_response['Quotes'] = sorted(request_response['Quotes'], key=lambda quote: quote['MinPrice']) #TODO verificar que funciona
    best_quote = request_response['Quotes'][0] #TODO error si no nhi ha

    get_carrier_names(best_quote, request_response)

    return best_quote


def get_best_quote(request_url):
    params = {'apiKey': api_key}
    response = requests.get(request_url, params=params).json()

    return get_result_and_build_json(response)


def generate_request_quotes(origin_place, destination_place, outbound_partial_date, inbound_partial_date, country=defaults['country'], currency=defaults['currency'], locale=defaults['locale']):
    origin_place_autocomplete = get_most_similar_id_result_autocomplete(origin_place)
    destination_place_autocomplete = get_most_similar_id_result_autocomplete(destination_place)

    req = flights_browse_prices.format(country, currency, locale, origin_place_autocomplete, destination_place_autocomplete, outbound_partial_date,
                                     inbound_partial_date)
    return req




if __name__ == '__main__':
    request_url = generate_request_quotes('pari', 'bcn', '2017-10-16', '2017-10-20')
    aux = get_best_quote(request_url)
    print(aux)