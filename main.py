import requests
import json
from datetime import datetime, timedelta
import os

if 'config.json' not in os.listdir():
    base = {
        "token": "",
        "workplace_id": "",
        "work_start": "08:00",
        "work_end": "17:00",
        "exceptions": [],
        "skip_weekends": True
    }
    with open('config.json', 'w+') as base_file:
        json.dump(base, base_file, indent=4)
        print('created base confing file. Add required information and restart.')
        exit(0)


config = dict()

try:
    with open('config.json', 'r') as conf_file:
        config = json.load(conf_file)
except Exception:
    print("config file not found!")
    exit(-1)


book_url = "https://kbc-frontend-api.iot.kapschcloud.net/api/Bookings/bookWorkplace/{}?tenantId=38"
confirm_url = 'https://kbc-frontend-api.iot.kapschcloud.net/api/Bookings/{}/confirm?tenantId=38'


headers = {
    'Authorization': f'Bearer {config["token"]}',
    'Content-Type': 'application/json'
}

# start_date = '2023-09-14'
# end_date = '2023-12-31'


def book_workplace(start_date, end_date, work_start, work_end, workplace_id,  skip_weekends=True, exceptions=[]):
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    bookings = dict()
    try:
        with open('bookings.json', 'r') as book_file:
            bookings = json.load(bookings)
    except Exception:
        print('no existing bookings found')

    while current_date <= end_date:
        if skip_weekends and current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
        if current_date.strftime('%Y-%m-%d') in exceptions:
            current_date += timedelta(days=1)
            continue

        work_start_time = datetime.strptime(
            f"{current_date.strftime('%Y-%m-%d')} {work_start}", '%Y-%m-%d %H:%M') - timedelta(hours=2)
        work_end_time = datetime.strptime(
            f"{current_date.strftime('%Y-%m-%d')} {work_end}", '%Y-%m-%d %H:%M') - timedelta(hours=2)

        start_time_str = work_start_time.strftime('%Y-%m-%dT%H:%M:%S') + "Z"
        end_time_str = work_end_time.strftime('%Y-%m-%dT%H:%M:%S') + "Z"

        print("Start Time:", start_time_str, ", End Time:", end_time_str)

        book_payload = json.dumps({
            "dateFrom": start_time_str,
            "dateTo": end_time_str,
            "licensePlate": ""
        })
        book_resp = requests.request(
            "POST", book_url.format(workplace_id), headers=headers, data=book_payload)

        if book_resp.status_code != 200:
            print(f"Failed to book on {current_date} Reason: ")
            print(book_resp.text)
            current_date += timedelta(days=1)
            continue

        print(f'Booked successfull for {current_date}')

        booking_id = book_resp.json()['bookingId']

        bookings[str(current_date).split(' ')[0]] = booking_id

        current_date += timedelta(days=1)

    with open('bookings.json', 'w+') as book_file:
        json.dump(bookings, book_file, indent=4)


def confirm_booking(booking_id=''):

    bookings = dict()
    try:
        with open('bookings.json', 'r') as book_file:
            bookings = json.load(book_file)
    except Exception:
        print('could not find booking for today!')
        return

    today = str(datetime.now().strftime('%Y-%m-%d'))
    try:
        booking_id = bookings[today]
    except KeyError:
        print('No Booking found for today!')
        return

    confirm_resp = requests.put(
        confirm_url.format(str(booking_id)), headers=headers)

    if confirm_resp.status_code != 200:
        print(f"Failed to confirm on {today}, Reason: ")
        print(confirm_resp.text, '\n')

    print(f'Confirm successfull for {today}')

    current_date += timedelta(days=1)


def show_help():
    help_message = '''
    Usage:
    - book [start_date] [end_date]: To book a workplace between start_date and end_date.
    - confirm [booking_id]: To confirm a booking with an optional booking ID. Optional. if not provided today will be confirmed
    - help: To display this help message.
    - exit: To exit the program.
    '''
    print(help_message)


if __name__ == '__main__':
    show_help()
    while True:
        user_input = input(">>: ").strip().split()

        if len(user_input) == 0:
            continue

        command = user_input[0].lower()

        if command == "book":
            if len(user_input) == 3:
                start_date = user_input[1]
                end_date = user_input[2]
                booking_id = book_workplace(
                    start_date, end_date, config['work_start'], config['work_end'], config['workplace_id'], config['skip_weekends'], config['exceptions'])
            else:
                print(
                    "Invalid number of arguments. Use 'book [start_date] [end_date]'.")

        elif command == "confirm":
            if len(user_input) <= 2:
                booking_id = user_input[1] if len(user_input) == 2 else None
                confirm_booking(booking_id)
            else:
                print(
                    "Invalid number of arguments. Use 'confirm [booking_id]'.")

        elif command == "help":
            show_help()

        elif command == "exit":
            print("Exiting the program.")
            break

        else:
            print("Unknown command. Type 'help' for available commands.")
