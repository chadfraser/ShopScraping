import requests
from lxml import html
import constants as c
import shared as sh


def main(headers):
    while True:
        search_parameter = get_user_search_query()
        names, prices, shipping, purchase_types, links = get_search_results(search_parameter, headers)
        if not names:
            continue
        total_prices = combine_base_and_shipping_prices(prices, shipping)
        list_of_buy_it_now, list_of_auctions = combine_item_data(names, total_prices, purchase_types, links)
        print_search_results(list_of_buy_it_now, list_of_auctions)
        while True:
            selection = get_user_ignore_selection(names)
            if selection == "q":
                break
            elif selection == "t":
                notification_price = get_notification_price(search_parameter)
                if notification_price:
                    add_element_to_tracking_file(search_parameter, notification_price)
                    break
            ignore_link = list_of_auctions[selection - 1][3]
            add_element_to_ignore_file(ignore_link)


def get_web_response(url, headers, xpath_string):
    web_response = requests.get(url, headers=headers)
    web_response.raise_for_status()
    parser = html.fromstring(web_response.text)
    results = parser.xpath(xpath_string)
    if not results:
        sh.print_then_sleep("Sorry, we didn't find any results for that.\n")
    return results


def get_search_results(search_parameter, headers):
    search_xpath = "//div[contains(@class, 'srp-river-main')]//li[contains(@class, 's-item') and not " \
                   "(preceding-sibling::div[@id = 'srp-river-results-message1'])]/div[contains(@class, " \
                   "'clearfix')]"
    name_xpath = ".//h3[contains(@class, 's-item__title')]/text()"
    price_xpath = ".//span[contains(@class, 's-item__price')]//text()"
    shipping_xpath = ".//span[contains(@class, 's-item__shipping')]//text()"
    purchase_type_xpath = ".//span[contains(@class, 's-item__purchase-options') or " \
                          "contains(@class, 's-item__time-left')]//text()"
    link_xpath = ".//a[contains(@class, 's-item__link')]/@href"
    search_url = f"https://www.ebay.ca/sch/i.html?_nkw={search_parameter.lower()}"

    results = get_web_response(search_url, headers, search_xpath)

    result_names = []
    result_prices = []
    result_shipping = []
    result_types = []
    result_links = []
    for result_data in results:
        name_data = result_data.xpath(name_xpath)
        price_data = result_data.xpath(price_xpath)
        shipping_data = result_data.xpath(shipping_xpath)
        purchase_type_data = result_data.xpath(purchase_type_xpath)
        link_data = result_data.xpath(link_xpath)
        if name_data:
            result_names.append(name_data[0])
            result_prices.append(price_data[0])
            result_shipping.append(shipping_data[0])
            result_types.append(purchase_type_data[0])
            result_links.append(link_data[0])
    return result_names, result_prices, result_shipping, result_types, result_links


def get_user_search_query():
    search_parameter = input("Please enter the name of the item you want to search for.\n")
    return search_parameter


def combine_item_data(names, prices, purchase_types, links):
    zipped_items = zip(names, prices, purchase_types, links)
    list_of_buy_it_now = [item for item in zipped_items if "left" not in item[2] and
                          not is_element_in_ignore_file(item[3])]
    list_of_auctions = [item for item in zipped_items if "left" in item[2] and
                        not is_element_in_ignore_file(item[3])]
    return list_of_buy_it_now, list_of_auctions


def print_search_results(list_of_buy_it_now, list_of_auctions):
    for num, (item, val, purchase_type, link) in enumerate(list_of_auctions):
        print(f"{num + len(list_of_buy_it_now):>2d}. ({val},  {purchase_type}) "
              f"{item if len(item) < 50 else item[:50] + '...'}")
        print("-----")
    for num, (item, val, purchase_type, link) in enumerate(list_of_buy_it_now):
        print(f"{num+1:>2d}. ({val},  {purchase_type}) {item if len(item) < 50 else item[:50] + '...'}")
    print()


def get_user_ignore_selection(list_of_auctions):
    while True:
        search_choice = input("Type in the number of the item you want to ignore while tracking, or type 't' to "
                              "select a price to track this search key at, or else type 'q' to search for another "
                              "item.\n")
        try:
            search_choice = int(search_choice)
            if not 0 < search_choice <= len(list_of_auctions):
                sh.print_then_sleep(f"That is not a valid input. Please ensure the chosen number is between 1 and "
                                    f"{len(list_of_auctions)}.\n")
            else:
                break
        except ValueError:
            if search_choice.lower() in ["q", "t"]:
                break
            sh.print_then_sleep("That is not a valid input. Please type a number from the available choices, type 't' "
                                "to track this search key, or else 'q' to quit.\n")
    return search_choice


def get_notification_price(key):
    while True:
        try:
            notification_price = float(input(f'What is the maximum price you want to track for "{key}"?\n'))
            if(sh.get_confirmation(f'Shall we send you notifications when items found under the search key "{key}" '
                                   f'are available for less than ${notification_price:.2f}?\n'
                                   f"(Input 'yes' or 'no')\n")):
                return notification_price
            else:
                return ""
        except ValueError:
            sh.print_then_sleep("Please type your answer in the form of a number. Do not include any currency symbols "
                                "or abbreviations.\n")


def update_file_if_already_tracked(key, new_price, file):
    with open(file, "r") as f:
        file_lines = f.readlines()
    for line_num, line_string in enumerate(file_lines):
        current_line = line_string.strip()
        if current_line == key:
            try:
                val = file_lines[line_num + 1].strip()
                if val in [str(round(new_price, 2)), str(round(new_price, 2)) + "0"]:
                    sh.print_then_sleep(f"You are already tracking {key} at a maximum price value of ${val}.\n")

                elif sh.get_confirmation(f"You are currently tracking {key} for a maximum price value of ${val}.\n"
                                         f"Would you like to update this maximum price value to ${new_price:.2f}?\n"):
                    file_lines[line_num + 1] = f"{new_price:.2f}\n"
                    with open(file, "w") as f:
                        f.writelines(file_lines)
                return True
            except IndexError:
                return False
    return False


def add_element_to_tracking_file(key, price):
    filename = "ebay_tracked_items.txt"
    try:
        if not update_file_if_already_tracked(key, price, filename):
            raise FileNotFoundError
    except FileNotFoundError:
        with open(filename, "a+") as f:
            f.write(f"{key}\n")
            f.write(f"{price:.2f}\n")


def is_element_in_ignore_file(link):
    filename = "ebay_ignored_items.txt"
    try:
        with open(filename, "r") as f:
            file_lines = [line.strip() for line in f.readlines()]
        if link in file_lines:
            return True
        return False
    except FileNotFoundError:
        return False


def add_element_to_ignore_file(link):
    filename = "ebay_ignored_items.txt"
    try:
        if is_element_in_ignore_file(link):
            print(f"{link} is already being ignored by this program.")
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        with open(filename, "a+") as f:
            f.write(f"{link}\n")


def combine_base_and_shipping_prices(base, shipping):
    base_cost_list, shipping_cost_list = convert_cost_strings_to_floats(base, shipping)
    total_price_list = get_total_price_list(base_cost_list, shipping_cost_list)
    return total_price_list


def convert_cost_strings_to_floats(base, shipping):
    base_cost_list = list(map(str.strip, base))
    shipping_cost_list = list(map(str.strip, shipping))
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


def get_total_price_list(base_cost_list, shipping_cost_list):
    total_price_list = []
    for base, shipping in zip(base_cost_list, shipping_cost_list):
        if isinstance(shipping, float):
            total_price_list.append(base + shipping)
        else:
            total_price_list.append(base)
    return total_price_list


if __name__ == "__main__":
    try:
        while True:
            main(c.main_headers)
            continuing = sh.get_confirmation("Would you like to track another search key?")
            if not continuing:
                break
    except requests.exceptions.HTTPError as e:
        sh.print_then_sleep(f"There was an error in getting the response from the server.\n{e}")
        input("Press 'enter' to close the program.")
    except requests.exceptions.RequestException as e:
        sh.print_then_sleep(f"There was a general error in processing the request.\n{e}")
        input("Press 'enter' to close the program.")
    except Exception as e:
        print(e)
        input()
