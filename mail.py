import smtplib
import sys
from email.message import EmailMessage
import shared as sh


def get_email_data():
    while True:
        try:
            with open("email-data.txt", "r") as f:
                data = f.readlines()
                from_email = data[0].strip()
                password = data[1].strip()
                to_email = data[2].strip()
            return from_email, password, to_email
        except FileNotFoundError:
            sh.print_then_sleep(f"Could not find 'email-data.txt' containing your username and password.")
            confirmation = sh.get_confirmation("Would you like to create this file?")
            if not confirmation:
                input("Press 'enter' to close the program.")
                sys.exit()
            create_email_data_file()
        except IndexError:
            sh.print_then_sleep(f"The file 'email-data.txt' did not contain all of the required lines.")
            confirmation = sh.get_confirmation("Would you like to try creating this file again?")
            if not confirmation:
                input("Press 'enter' to close the program.")
                sys.exit()
            create_email_data_file()


def create_email_data_file():
    from_email = input("Please type in the full email address you want to send emails from. This must be your own "
                       "email address.")
    password = input("Please type in the password to this email address. Note that this will be saved as plain text.")
    to_email = input("Please type in the full email address you want to send notification emails to. Please get the "
                     "permission of the holder of that email address first.")
    with open("email-data.txt", "w") as f:
        f.write(f"{from_email}\n{password}\n{to_email}")


def send_email(mail):
    try:
        # with smtplib.SMTP("smtp.gmail.com", 587) as server:
        # with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
        with smtplib.SMTP("smtp.office365.com", 587) as server:
            server.ehlo()
            server.starttls()
            email, password = get_email_data()[:2]
            server.login(email, password)
            server.send_message(mail)
    except smtplib.SMTPAuthenticationError as e:
        sh.print_then_sleep(f"There was an error in authentication. Double check your username and password.\n{e}")
        input("Press 'enter' to close the program.")
    except smtplib.SMTPException as e:
        sh.print_then_sleep(f"An SMTP error occurred.\n{e}")
        input("Press 'enter' to close the program.")


def compose_email(message_data="No data", subject="No subject"):
    msg = EmailMessage()
    msg.set_content(message_data)
    msg['Subject'] = subject
    email_address = get_email_data()[0]
    msg['From'] = email_address
    msg['To'] = get_email_data()[2]
    send_email(msg)


if __name__ == "__main__":
    compose_email()
