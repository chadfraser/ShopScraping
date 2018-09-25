import requests
from lxml import html
import re
import constants as c
import shared as sh


def main(headers):
    while True:
        names, prices, links = get_user_search_query(headers)
        if not names:
            continue
        print_search_results(names, prices)
        selection = get_user_search_selection(names)
        if selection == "q":
            continue
        desired_name = names[selection - 1]
        desired_link = links[selection - 1]
        notification_price = get_notification_price(desired_name)
        desired_link = get_quality_to_track(desired_link)
        if notification_price:
            add_element_to_tracking_file(desired_name, desired_link, notification_price)
            break


def get_web_response(url, headers, xpath_string):
    web_response = requests.get(url, headers=headers)
    web_response.raise_for_status()
    parser = html.fromstring(web_response.text)
    results = parser.xpath(xpath_string)
    if not results:
        sh.print_then_sleep("Sorry, we didn't find any results for that.\n")
    return results


def get_search_results(keyword, headers):
    search_xpath = "//div[contains(@class, 's-item-container') and not " \
                   "(descendant::*[contains(@class, 's-sponsored-header')])]"
    result_xpath = ".//h2[contains(@class, 's-access-title')]/text()"

    # The price_xpath is split into three parts: It picks up data containing the current price (under the class
    # 'a-color-price'), data where the only price listed for the item is the suggested retail price (under the class
    # 'a-text-strike'), and data where there is no listed price (which contains the text 'Currently unavailable').
    price_xpath = ".//span[contains(@class, 'a-color-price')]/text() |" \
                  ".//span[contains(@class, 'a-text-strike') and contains(@aria-label, 'Suggested Retail')]/text() |" \
                  ".//span[contains(@class, 'a-color-secondary') and . = 'Currently unavailable']/text()"
    link_xpath = ".//a[contains(@class, 's-color-twister-title-link')]/@href"
    search_url = f"https://www.amazon.ca/s/field-keywords={keyword.lower()}"

    results = get_web_response(search_url, headers, search_xpath)

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
            offer_link = get_offer_listing_url(link_data[0])
            result_links.append(offer_link)
    return result_names, result_prices, result_links


def get_user_search_query(headers):
    search_parameter = input("Please enter the name of the item you want to search for.\n")
    names, prices, links = get_search_results(search_parameter, headers=headers)
    return names, prices, links


def print_search_results(names, prices):
    for num, (item, val) in enumerate(zip(names, prices)):
        print(f"{num+1:>2d}. ({val}) {item if len(item) < 50 else item[:50] + '...'}")
    print()


def get_user_search_selection(names):
    while True:
        search_choice = input("Type in the number of the item you want to track, or else type 'q' to search for "
                              "another item.\n")
        try:
            search_choice = int(search_choice)
            if not 0 < search_choice <= len(names):
                sh.print_then_sleep(f"That is not a valid input. Please ensure the chosen number is between 1 and "
                                    f"{len(names)}.\n")
            else:
                break
        except ValueError:
            if search_choice.lower() == "q":
                break
            sh.print_then_sleep("That is not a valid input. Please type a number from the available choices, or else "
                                "'q' to quit.\n")
    return search_choice


def get_notification_price(name):
    while True:
        try:
            notification_price = float(input(f'What is the maximum price you want to track for "{name}"?\n'))
            if(sh.get_confirmation(f'Shall we send you notifications when "{name}" is available for less than '
                                   f'${notification_price:.2f}?\n'
                                   f"(Input 'yes' or 'no')\n")):
                return notification_price
            else:
                return ""
        except ValueError:
            sh.print_then_sleep("Please type your answer in the form of a number. Do not include any currency symbols "
                                "or abbreviations.\n")


def update_file_if_already_tracked(name, link, new_price, file):
    with open(file, "r") as f:
        file_lines = f.readlines()
    for line_num, line_string in enumerate(file_lines):
        current_line = line_string.strip()
        if sh.is_link(line_string.strip()) and get_offer_listing_url(current_line) == get_offer_listing_url(link):
            try:
                val = file_lines[line_num + 1].strip()
                previous_conditions = convert_link_to_conditions(current_line)
                new_conditions = convert_link_to_conditions(link)
                if val in [str(round(new_price, 2)), str(round(new_price, 2)) + "0"] and \
                        previous_conditions == new_conditions:
                    sh.print_then_sleep(f"You are already tracking {name} at a maximum price value of ${val}.\n")

                elif sh.get_confirmation(f"You are currently tracking {name} for a maximum price value of ${val}, "
                                         f"at these conditions: {', '.join(previous_conditions) or 'all'}.\n"
                                         f"Would you like to update this maximum price value to ${new_price:.2f} "
                                         f"at these conditions: {', '.join(new_conditions) or 'all'}?\n"):
                    file_lines[line_num] = f"{link}\n"
                    file_lines[line_num + 1] = f"{new_price:.2f}\n"
                    with open(file, "w") as f:
                        f.writelines(file_lines)
                return True
            except IndexError:
                return False
    return False


def get_offer_listing_url(link):
    split_link = link.split("/")
    product_code = split_link[5]
    new_link = f"https://www.amazon.ca/gp/offer-listing/{product_code}/"
    return new_link


def add_element_to_tracking_file(name, link, price):
    filename = "amazon_tracked_items.txt"
    try:
        if update_file_if_already_tracked(name, link, price, filename):
            return
        raise FileNotFoundError
    except FileNotFoundError:
        with open("amazon_tracked_items.txt", "a+") as f:
            f.write(f"{name}\n")
            f.write(f"{link}\n")
            f.write(f"{price:.2f}\n")


def get_user_input_for_quality():
    while True:
        sh.print_then_sleep("What conditions of this item are you interested in tracking?\n"
                            "From highest to lowest quality, possible conditions are:\n"
                            "\tNew        (n)\n"
                            "\tLike New   (l)\n"
                            "\tVery Good  (v)\n"
                            "\tGood       (g)\n"
                            "\tAcceptable (a)\n"
                            "\tAll        (x)""")
        response = input("Please type the key letters for all conditions you are interested in tracking.\n"
                         "For example, if you want to track only new, like new, and very good conditions, type "
                         "'nlv'.\n").lower()
        if [i for i in set(response) if i in c.abbreviated_quality_dict]:
            return response
        sh.print_then_sleep("There was an error in your input. You did not include any condition key letters.\n")


def get_quality_to_track(link):
    quality = set(get_user_input_for_quality())
    final_link = get_link_with_quality(link, quality)
    return final_link


def get_link_with_quality(link, condition_set):
    link_list = [link]
    if "x" in condition_set or not condition_set:
        return link
    link_list.append("ref=?")
    for letter in condition_set:
        if letter in c.abbreviated_quality_dict:
            link_list.append(f"f_{c.abbreviated_quality_dict[letter]}=true&")
    return "".join(link_list)


def convert_link_to_conditions(link):
    conditions = set()
    split_link = link.split("/")
    if len(split_link) < 6:
        return {"x"}
    condition_information = split_link[-1]
    condition_information = re.split('[?&]', condition_information)
    for element in condition_information[1:]:
        if element[2:-5] in c.full_quality_dict:
            conditions.add(c.full_quality_dict[element[2:-5]])
    return conditions


if __name__ == "__main__":
    try:
        while True:
            main(c.main_headers)
            continuing = sh.get_confirmation("Would you like to search for another item to track?")
            if not continuing:
                break
    except requests.exceptions.HTTPError as e:
        sh.print_then_sleep(f"There was an error in getting the response from the server.\n{e}")
        input("Press 'enter' to close the program.")
    except requests.exceptions.RequestException as e:
        sh.print_then_sleep(f"There was a general error in processing the request.\n{e}")
        input("Press 'enter' to close the program.")
