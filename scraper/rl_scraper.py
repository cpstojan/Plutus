# Unofficial package providing Python API for coinbase
# https://github.com/danpaquin/coinbasepro-python
import cbpro

import time
import math
import pandas as pd
import os

# For config file
import yaml

# For email sending
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart


def email_notification(email_subject):
    with open('config.yaml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"

    msg = MIMEMultipart()
    msg['From'] = config['email']
    msg['To'] = config['to']
    msg['Subject'] = config['hostname'] + ': ' + email_subject

    # Create a secure SSL context
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(config['email'], config['password'])
        server.sendmail(config['email'], config['to'], msg.as_string())


def scraper(security='BTC-USD', request_time=10, dump_time=3600, send_email=True):
    # BASH script should automatically restart upon any failures
    # Therefore we send an email on reconnect and disconnect
    email_notification('RECONNECT DETECTED')

    public_client = cbpro.PublicClient()

    # Get the current working directory for print statement
    path = os.getcwd()

    historical_ob = pd.DataFrame(columns=['Time', 'Bids', 'Asks'])

    while True:
        try:
            cur_time = math.floor(time.time())
            if cur_time % request_time == 0:
                # Get the order book at level_2 granularity - this is the top 50 bids and asks
                ob = public_client.get_product_order_book(security, 2)

                # Pandas allows for enlargement using loc
                historical_ob.loc[len(historical_ob)] = [cur_time, ob['bids'], ob['asks']]

                # Every hour collected data is flushed to a csv, cleared, and continued
                if cur_time % dump_time == 0:
                    file_name = str(cur_time) + '.csv'
                    historical_ob.to_csv(file_name, index=False)
                    # ToDo: Save to Google Drive
                    print('File:', cur_time, 'saved in', path)
                    historical_ob.drop(historical_ob.index, inplace=True)

                # Ensures only 1 call every 10 seconds - additionally that calls are evenly
                # spaced even when flushing every hour which will take substantially longer
                # running under assumption that a flush is less than 9 seconds plus overhead
                # of first call
                time.sleep(1)
        except:
            print('Error hit')
            if send_email:
                print('Sending email to restart')
                email_notification('DISCONNECT DETECTED')

            print('Saving partial historical order book')
            file_name = str(cur_time) + '.csv'
            historical_ob.to_csv(file_name, index=False)
            print('File:', cur_time, 'saved in', path)

            return -1


def main():
    scraper()


if __name__ == '__main__':
    main()
