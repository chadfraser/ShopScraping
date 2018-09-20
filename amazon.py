import requests
from lxml import html


def parse_amazon(url, header):
    response = requests.get(url, headers=header)
    parser = html.fromstring(response.text)
    sellers = parser.xpath("//div[contains(@class, 'a-row a-spacing-mini olpOffer')]")
    if not sellers:
        return
    base_cost, shipping_cost = get_base_and_shipping_costs(sellers)
    base_cost_floats, shipping_cost_floats = convert_cost_to_float(base_cost, shipping_cost)
    total_price_list = get_total_price_list(base_cost_floats, shipping_cost_floats)
    return total_price_list


def get_base_and_shipping_costs(sellers):
    base_xpath = ".//span[contains(@class, 'olpOfferPrice')]/text()"

    # The ship_xpath is split into two parts: It picks up data containing the shipping price (under the class
    # 'olpShippingPrice') and picks up data where there free shipping (which contains the text 'FREE Shipping').
    ship_xpath = ".//p[contains(@class, 'olpShippingInfo')]//span[contains(@class, 'olpShippingPrice')][1]//text() |"\
                 " //span[contains(@class, 'a-color-secondary')]//*[contains(., 'FREE Shipping')]//text()"

    base_cost = []
    shipping_cost = []
    for seller_data in sellers:
        base_cost.append(seller_data.xpath(base_xpath)[0])
        shipping_cost.append(seller_data.xpath(ship_xpath)[0])
    return base_cost, shipping_cost


def get_total_price_list(base_cost_list, shipping_cost_list):
    total_price_list = []
    for base, shipping in zip(base_cost_list, shipping_cost_list):
        if isinstance(shipping, float):
            total_price_list.append(base + shipping)
        else:
            total_price_list.append(base)
    return total_price_list


def convert_cost_to_float(base_cost, shipping_cost):
    base_cost_list = list(map(str.strip, base_cost))
    shipping_cost_list = list(map(str.strip, shipping_cost))
    temp = []
    for cost in base_cost_list:
        cost = float(cost.split()[-1])
        temp.append(cost)
    base_cost_list = temp

    temp = []
    for cost in shipping_cost_list:
        try:
            cost = float(cost.split()[-1])
        except ValueError:
            pass
        temp.append(cost)
    shipping_cost_list = temp
    return base_cost_list, shipping_cost_list


# url = 'https://www.amazon.ca/gp/offer-listing/B01MUAGZ49'
url_1 = 'https://www.amazon.ca/gp/offer-listing/B01MUAGZ49/ref=olp_f_usedVeryGood&f_new=true&f_collectible=true&' \
        'f_usedLikeNew=true&f_usedVeryGood=true'
url_2 = 'https://www.amazon.ca/gp/offer-listing/B01LTHP2ZK/ref=olp_f_usedVeryGood&f_new=true&f_collectible=true&' \
        'f_usedLikeNew=true&f_usedVeryGood=true'

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}
prices = parse_amazon(url_1, headers)
print(prices)

# ref=sr_nr_p_n_shipping_option-bin_1
# olpOfferPrice
# olpShippingPrice
# olpCondition
# olpSellerColumn
