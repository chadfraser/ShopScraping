import compare_amazon as comp_az
import constants as c
import mail


def check_amazon_tracked_prices():
    composition = []
    names, urls, min_prices = read_amazon_tracked_data()
    if names:
        for (url, name, min_price) in zip(urls, names, min_prices):
            selling_prices, seller_names = comp_az.parse_amazon(url, c.main_headers)
            composition = add_to_email_composition(composition, selling_prices, seller_names, min_price, name)
    if composition:
        subject = "Some items you are tracking on Amazon are now on sale!"
        mail.compose_email(composition, subject)


def read_amazon_tracked_data():
    names = []
    urls = []
    min_prices = []
    try:
        with open("amazon_tracked_items.txt", "r") as f:
            lines = f.readlines()
            names = lines[0::3]
            urls = lines[1::3]
            min_prices = lines[2::3]
    except FileNotFoundError:
        pass
    return names, urls, min_prices


def add_to_email_composition(composition, selling_prices, seller_names, min_price, item_name):
    if any(selling_price < min_price for selling_price in selling_prices):
        composition.append(f"We have found {item_name} available for less than {min_price}.\n")
        for current_price, current_name in zip(selling_prices, seller_names):
            if current_price < min_price:
                composition.append(f"{current_name} is selling {item_name} for ${current_price}.\n")
    return composition
