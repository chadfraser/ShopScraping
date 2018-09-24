import requests
from lxml import html
import time
import traceback


def print_then_sleep(message):
    print(message)
    time.sleep(1.25)


def parse_amazon(url, headers):
    response = requests.get(url, headers=headers)
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
    # 'olpShippingPrice') and picks up data where there is free shipping (which contains the text 'FREE Shipping').
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


def get_search_results(keyword, headers):
    result_xpath = ".//h2[contains(@class, 's-access-title')]/text()"
    price_xpath = ".//span[contains(@class, 'a-color-price')]/text() |" \
                  ".//span[contains(@class, 'a-text-strike') and contains(@aria-label, 'Suggested Retail')]/text() |" \
                  ".//span[contains(@class, 'a-color-secondary') and . = 'Currently unavailable']/text()"
    link_xpath = ".//a[contains(@class, 's-color-twister-title-link')]/@href"

    search_url = f"https://www.amazon.ca/s/field-keywords={keyword.lower()}"
    response = requests.get(search_url, headers=headers)
    parser = html.fromstring(response.text)
    results = parser.xpath("//div[contains(@class, 's-item-container') and not "
                           "(descendant::*[contains(@class, 's-sponsored-header')])]")
    if not results:
        print_then_sleep("Sorry, we didn't find any results for that.\n")
        return None, None, None

    result_names = []
    result_prices = []
    result_links = []
    for result_data in results:
        data = result_data.xpath(result_xpath)
        price_data = result_data.xpath(price_xpath)
        link_data = result_data.xpath(link_xpath)
        if data:
            result_names.append(data[0])
            result_prices.append(price_data[0])
            result_links.append(link_data[0])
    return result_names, result_prices, result_links


def get_user_search_query(headers):
    search_parameter = input("Please enter the name of the item you want to search for.\n")
    names, prices, links = get_search_results(search_parameter, headers=headers)
    return names, prices, links


def print_search_results(names, prices, links):
    for num, (item, val, link) in enumerate(zip(names, prices, links)):
        print(f"{num+1:>2d}. ({val}) {item if len(item) < 50 else item[:50] + '...'}")
    print()


def get_user_search_selection(names):
    while True:
        search_choice = input("Type in the number of the item you want to track, or else type 'q' to search for "
                              "another item.\n")
        try:
            search_choice = int(search_choice)
            if not 0 < search_choice <= len(names):
                print_then_sleep(f"That is not a valid input. Please ensure the chosen number is between 1 and "
                                 f"{len(names)}\n.")
            else:
                break
        except ValueError:
            if search_choice.lower() == "q":
                search_choice = 0
                break
            print_then_sleep("That is not a valid input. Please type a number from the available choices, or else "
                             "'q' to quit.\n")
    return search_choice


def get(headers):
    while True:
        names, prices, links = get_user_search_query(headers)
        if not names:
            continue
        print_search_results(names, prices, links)
        selection = get_user_search_selection(names)
        if selection == 0:
            continue
        desired_name = names[selection - 1]
        desired_link = links[selection - 1]
        notification_price = get_notification_price(desired_name)
        if notification_price:
            add_element_to_track_file(desired_name, desired_link, notification_price)


def get_notification_price(name):
    while True:
        try:
            notification_price = float(input(f'What is the maximum price you want to track for "{name}"?\n'))
            if(get_confirmation(f'Shall we send you notifications when "{name}" is available for less than '
                                f'${notification_price:.2f}?\n'
                                f"(Input 'yes' or 'no')\n")):
                return notification_price
            else:
                return ""
        except ValueError:
            print("Please type your answer in the form of a number. Do not include any currency symbols or "
                  "abbreviations.\n")
            time.sleep(2)


def get_confirmation(message):
    while True:
        confirm = input(message)
        if confirm.lower() in ['yes', 'y']:
            return True
        elif confirm.lower() in ['no', 'n']:
            return False
        print_then_sleep("That is not a valid response.\n")


def update_price_if_already_tracked(name, new_price, file):
    with open(file, "r") as f:
        file_lines = f.readlines()
    for line_num, line_string in enumerate(file_lines):
        if line_string.strip() == name:
            try:
                val = file_lines[line_num + 2].strip()
                if val == new_price:
                    print_then_sleep(f"You are already tracking {name} at a maximum price value of ${val}.\n")
                elif get_confirmation(f"You are currently tracking {name} for a maximum price value of ${val}.\n"
                                      f"Would you like to update this maximum price value to ${new_price:.2f}?\n"):
                    file_lines[line_num + 2] = f"{new_price:.2f}\n"
                    with open(file, "w") as f:
                        f.writelines(file_lines)
                return True
            except IndexError:
                return False
    return False


def add_element_to_track_file(name, link, price):
    filename = "amazon_tracked_items.txt"
    try:
        if update_price_if_already_tracked(name, price, filename):
            return
        raise FileNotFoundError
    except FileNotFoundError:
        with open("amazon_tracked_items.txt", "a+") as f:
            f.write(f"{name}\n")
            f.write(f"{link}\n")
            f.write(f"{price:.2f}\n")


if __name__ == "__main__":
    main_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}

    while True:
        get(main_headers)

        # if names:

    # for num, (item, val, link) in enumerate(zip(names, prices, links)):
    #     print(f"{num+1:>2d}. ({val}) {item if len(item) < 50 else item[:50] + '...'}")
    # search_choice = input("Type in the number of the item you want to track, or else type 'q' to search for another "
    #                       "item.")
    # input()

#     # url = 'https://www.amazon.ca/gp/offer-listing/B01MUAGZ49'
#     url_1 = 'https://www.amazon.ca/gp/offer-listing/B01MUAGZ49/ref=olp_f_usedVeryGood&f_new=true&f_collectible=true&' \
#             'f_usedLikeNew=true&f_usedVeryGood=true'
#     url_2 = 'https://www.amazon.ca/gp/offer-listing/B01LTHP2ZK/ref=olp_f_usedVeryGood&f_new=true&f_collectible=true&' \
#             'f_usedLikeNew=true&f_usedVeryGood=true'
#     prices = parse_amazon(url_1, headers)
#     prices = parse_amazon(url_2, headers)

# ref=sr_nr_p_n_shipping_option-bin_1
# olpOfferPrice
# olpShippingPrice
# olpCondition
# olpSellerColumn
#smo x2, tomotoc, botw, mk8 deluxe, joycon l/r,
# Super Mario Party missing price
# tomotoc missing all
