# Unofficial package providing Python API for coinbase
# https://github.com/danpaquin/coinbasepro-python
import cbpro
import time
import math
import pandas as pd


def main():
    public_client = cbpro.PublicClient()

    historical_ob = pd.DataFrame(columns=['Time', 'Bids', 'Asks'])

    while True:
        cur_time = math.floor(time.time())
        if cur_time % 10 == 0:
            # Get the order book at level_2 granularity - this is the top 50 bids and asks
            ob = public_client.get_product_order_book('BTC-USD', 2)

            # Pandas allows for enlargement using loc
            historical_ob.loc[len(historical_ob)] = [cur_time, ob['bids'], ob['asks']]

            # Every hour collected data is flushed to a csv, cleared, and continued
            if cur_time % 3600 == 0:
                # historical_ob.to_csv()
                print(historical_ob)
                historical_ob.drop(historical_ob.index, inplace=True)

            # Ensures only 1 call every 10 seconds - additionally that calls are evenly
            # spaced even when flushing every hour which will take substantially longer
            # running under assumption that a flush is less than 9 seconds plus overhead
            # of first call
            time.sleep(1)


if __name__ == '__main__':
    main()
