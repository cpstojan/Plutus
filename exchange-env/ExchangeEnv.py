from abc import ABC
from gym import spaces
from ast import literal_eval

import pandas as pd
import numpy as np

import math
import os
import gym


class ExchangeEnv(gym.Env, ABC):
    """
    A OpenAI gym environment allowing to simulate trading
    using level 2/3 data (depth of order book)
    """

    def __init__(self, directory, cash, security):
        super().__init__()

        # Historical data is loaded here
        self.data = pd.DataFrame

        # Historical observations are held here
        self.historical_obs = []

        # Starting balances of cash and security being traded
        self.cash = cash
        self.security = security

        self.step = 0

        # Actions take the form of a pair (Action, Percentage)
        #   Action: buy -> 0, sell -> 1, hold -> 2
        #   Percentage: percentage of holding (if action is hold this is ignored)
        self.action_space = spaces.Box(low=np.array([np.float32(0), np.float32(0)]),
                                       high=np.array([np.float32(2), np.float32(1)]), dtype=np.float32)

        # Observation space is a triple containing
        #   Highest bid
        #   Lowest ask
        #   TV-IMBAL
        #   This triple is given at t, t-1, t-10, and t-100
        self.observation_space = spaces.Box(high=np.float32(math.inf), low=np.float32(0),
                                            shape=(4, 3), dtype=np.float32)

        self.__data_loader(directory)

    def __data_loader(self, directory):
        """
        Given an absolute path to directory of historical order book
        data - loads each CSV into panda dataframe

        Runs under the assumption that rows are in sorted order by
        time and of the form [Time, Bids, Asks]

        :param directory: Absolute path to directory of historical
        order book data
        :return: NULL
        """
        data = pd.DataFrame()
        for filename in os.listdir(directory):
            if not filename.endswith('.csv'):
                continue
            else:
                filepath = os.path.join(directory, filename)
                data = data.append(pd.read_csv(filepath), ignore_index=True)

        self.data = data

    def __next_observation(self):
        current_step = self.data.iloc[self.step]
        current_bids = [list(map(float, i)) for i in literal_eval(current_step['Bids'])]
        current_asks = [list(map(float, i)) for i in literal_eval(current_step['Asks'])]

        max_bid = max(current_bids, key=lambda item: item[0])[0]
        min_ask = min(current_asks, key=lambda item: item[0])[0]

        sum_bid = sum([bid[1] for bid in current_bids])
        sum_ask = sum([ask[1] for ask in current_asks])
        print("Sum of bids is", sum_bid)
        print("Sum of asks is", sum_ask)
        tv_imbal = (sum_ask - sum_bid) / (sum_ask + sum_bid)

        self.historical_obs.append([max_bid, min_ask, tv_imbal])

        if len(self.historical_obs) < 2:
            frame = np.array([
                np.array(self.historical_obs[self.step]),
                np.zeros([3]),
                np.zeros([3]),
                np.zeros([3])
            ])
        elif len(self.historical_obs) < 10:
            frame = np.array([
                self.historical_obs[self.step],
                self.historical_obs[self.step - 1],
                np.zeros([3]),
                np.zeros([3])
            ])
        elif len(self.historical_obs) < 100:
            frame = np.array([
                self.historical_obs[self.step],
                self.historical_obs[self.step - 1],
                self.historical_obs[self.step - 10],
                np.zeros([3])
            ])
        else:
            frame = np.array([
                self.historical_obs[current_step],
                self.historical_obs[current_step - 1],
                self.historical_obs[current_step - 10],
                self.historical_obs[current_step - 100],
            ])

        return frame

    def clearing_house(self, cash_amount=0, security_amount=0):
        current_step = self.data.iloc[self.step]

        cash_gained = 0
        security_gained = 0

        if cash_amount > 0:
            # If a security is being purchased the asks is what I care about
            # We want the lowest ask first
            current_asks = [list(map(float, i)) for i in literal_eval(current_step['Asks'])]
            current_asks.sort(key=lambda x: x[0])
            print(current_asks)

            depth = 0
            while cash_amount > 0:
                able_to_purchase = cash_amount / current_asks[depth][0]

                # if we are able to purchase more than is offered we move
                # to the next depth of book
                if able_to_purchase > current_asks[depth][1]:
                    security_gained += current_asks[depth][1]
                    cash_amount -= current_asks[depth][0] * current_asks[depth][1]
                    depth += 1
                else:
                    security_gained += able_to_purchase
                    cash_amount = 0

        if security_amount > 0:
            # If a security is being sold the bids is what I care about
            # We want the highest bid first
            current_bids = [list(map(float, i)) for i in literal_eval(current_step['Bids'])]
            current_bids.sort(key=lambda x: x[0], reverse=True)
            print(current_bids)

        return cash_gained, security_gained

    def __take_action(self, action):
        order = action[0]
        percent = action[1]

        # if action_type < 1 then it is of type buy
        if order < 1:
            # Cash value of order is cash on hand * percent
            cash_amount = self.cash * percent
            self.__clearing_house(cash_amount=cash_amount)

        elif order < 2:
            # Sell amount % of shares held
            security_amount = self.security * percent
            self.__clearing_house(security_amount=security_amount)

        self.net_worth = self.balance + self.shares_held * current_price

        if self.net_worth > self.max_net_worth:
            self.max_net_worth = self.net_worth

        if self.shares_held == 0:
            self.cost_basis = 0


env = ExchangeEnv(r"C:\Users\chris\OneDrive\Documents\GitHub\Plutus\data", 0, 0)
print(env.clearing_house(cash_amount=2500))
