import requests
from lxml import html


def parse_ebay(url, header):
    response = requests.get(url, headers=header)
    print(response)
    parser = html.fromstring(response.text)
    sellers = parser.xpath("//div[contains(@class, 'srp-river-main')]//li[contains(@class, 's-item') and not "
                           "(preceding-sibling::div[@id = 'srp-river-results-message1'])]/div[contains(@class,"
                           "'clearfix')]")
    if not sellers:
        return
    title, base_cost, shipping_cost, purchase_type = get_item_data(sellers)
    base_cost_list, shipping_cost_list = convert_cost_to_float(base_cost, shipping_cost)
    total_price_list = get_total_price_list(base_cost_list, shipping_cost_list)
    return total_price_list


def get_item_data(sellers):
    title_xpath = ".//h3[contains(@class, 's-item__title')]//text()"
    base_xpath = ".//span[contains(@class, 's-item__price')]//text()"
    ship_xpath = ".//span[contains(@class, 's-item__shipping')]//text()"
    # Buy It Now, or Best offer, X bids
    purchase_type_xpath = ".//span[contains(@class, 's-item__purchase-options') or " \
                          "contains(@class, 's-item__bidCount')]//text()"

    title = []
    base_cost = []
    shipping_cost = []
    purchase_type = []
    for seller_data in sellers:
        title.append(seller_data.xpath(title_xpath)[0])
        base_cost.append(seller_data.xpath(base_xpath)[0])
        shipping_cost.append(seller_data.xpath(ship_xpath)[0])
        purchase_type.append(seller_data.xpath(purchase_type_xpath)[0])
    return title, base_cost, shipping_cost, purchase_type


def get_total_price_list(base_cost_list, shipping_cost_list):
    total_price_list = []
    for base, shipping in zip(base_cost_list, shipping_cost_list):
        if isinstance(shipping, float):
            total_price_list.append(base + shipping)
        else:
            total_price_list.append(base)
    return total_price_list


def convert_cost_to_float(base_cost_list, shipping_cost_list):
    temp = []

    for cost in base_cost_list:
        cost = float(cost.split()[1][1:])
        temp.append(cost)
    base_cost_list = temp

    temp = []
    for cost in shipping_cost_list:
        try:
            cost = float(cost.split()[1][1:])
        except ValueError:
            pass
        temp.append(cost)
    shipping_cost_list = temp
    return base_cost_list, shipping_cost_list


# after #srp-river-results,   .s-item,   .s-item__info,  .s-item__title   (h3, text)
    # .s-item__details,  .s-item__price (text),   .s-item__shipping (text),   .s-item__purchase-options  (text) (span)
    # Buy It Now
    # .s-item__time, .clipped "Time Left",  .s-item__time-left (text, span: 4d 3h left),  .s-item__time-end (text, span)
                # (Fri., 8:36 p.m.)
                # .s-item__bid-count (text, span)

url_ebay = 'https://www.ebay.ca/sch/139971/i.html?_fsrp=1&_sacat=139971&_nkw=nintendo%20switch%20console&' \
           'LH_ItemCondition=1000&_sop=12&rt=nc&_udlo=200&_udhi=350'

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}
print(parse_ebay(url_ebay, headers))
