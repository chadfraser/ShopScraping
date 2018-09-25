import track_amazon as az


def parse_amazon(url, headers):
    sellers_xpath = "//div[contains(@class, 'a-row a-spacing-mini olpOffer')]"
    sellers = az.get_web_response(url, headers, sellers_xpath)
    if not sellers:
        return
    base_cost, shipping_cost, seller_names = get_costs_and_seller_name(sellers)
    base_cost_floats, shipping_cost_floats = convert_cost_to_float(base_cost, shipping_cost)
    total_price_list = get_total_price_list(base_cost_floats, shipping_cost_floats)
    return total_price_list, seller_names


def get_costs_and_seller_name(sellers):
    base_xpath = ".//span[contains(@class, 'olpOfferPrice')]/text()"

    # The ship_xpath is split into two parts: It picks up data containing the shipping price (under the class
    # 'olpShippingPrice') and picks up data where there is free shipping (which contains the text 'FREE Shipping').
    ship_xpath = ".//p[contains(@class, 'olpShippingInfo')]//span[contains(@class, 'olpShippingPrice')][1]//text() |" \
                 " //span[contains(@class, 'a-color-secondary')]//*[contains(., 'FREE Shipping')]//text()"
    seller_name_xpath = ".//h3[contains(@class, 'olpSellerName')]//a/text() |" \
                        ".//h3[contains(@class, 'olpSellerName')]/img/@alt"

    base_cost = []
    shipping_cost = []
    seller_names = []
    for seller_data in sellers:
        base_cost.append(seller_data.xpath(base_xpath)[0])
        shipping_cost.append(seller_data.xpath(ship_xpath)[0])
        seller_names.append(seller_data.xpath(seller_name_xpath)[0])
    return base_cost, shipping_cost, seller_names


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


def get_total_price_list(base_cost_list, shipping_cost_list):
    total_price_list = []
    for base, shipping in zip(base_cost_list, shipping_cost_list):
        if isinstance(shipping, float):
            total_price_list.append(base + shipping)
        else:
            total_price_list.append(base)
    return total_price_list
