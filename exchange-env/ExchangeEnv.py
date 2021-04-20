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

    def __init__(self, directory, cash, security, debug=False):
        super().__init__()

        # Historical data is loaded here
        self.data = pd.DataFrame

        # Historical observations are held here
        self.historical_obs = []

        # Starting balances of cash and security being traded
        self.cash = cash
        self.security = security

        self.time_step = 0

        # Actions take the form of a pair (Action, Percentage)
        #   Action: buy -> 0, sell -> 1, hold -> 2
        #   Percentage: percentage of holding (if action is hold this is ignored)
        self.action_space = spaces.Box(low=np.array([np.float32(0), np.float32(0)]),
                                       high=np.array([np.float32(3), np.float32(1)]), dtype=np.float32)

        # Observation space is a triple containing
        #   Highest bid
        #   Lowest ask
        #   TV-IMBAL
        #   This triple is given at t, t-1, t-10, and t-100
        self.observation_space = spaces.Box(high=np.float32(math.inf), low=np.float32(0),
                                            shape=(4, 3), dtype=np.float32)

        self.__data_loader(directory)

        # Used for calculating when we are done going through data
        self.final_step = len(self.data) - 1

        # Original values are saved for a reset
        self.starting_cash = cash
        self.starting_security = security

        # Logging to allow user to see behavior of agent
        # This will be in the form of tuples:
        #   tuple[0] - [action, percentage]
        #   tuple[1] - portfolio value
        #   tuple[2] - [highest bid, lowest ask, TV-IMBAL
        self.historical_behaviour = []

        # Enables additional print statements
        self.debug = debug

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
        current_step = self.data.iloc[self.time_step]
        current_bids = [list(map(float, i)) for i in literal_eval(current_step['Bids'])]
        current_asks = [list(map(float, i)) for i in literal_eval(current_step['Asks'])]

        max_bid = max(current_bids, key=lambda item: item[0])[0]
        min_ask = min(current_asks, key=lambda item: item[0])[0]

        sum_bid = sum([bid[1] for bid in current_bids])
        sum_ask = sum([ask[1] for ask in current_asks])

        tv_imbal = (sum_ask - sum_bid) / (sum_ask + sum_bid)

        self.historical_obs.append([max_bid, min_ask, tv_imbal])

        if len(self.historical_obs) < 2:
            frame = np.array([
                np.array(self.historical_obs[self.time_step]),
                np.zeros([3]),
                np.zeros([3]),
                np.zeros([3])
            ])
        elif len(self.historical_obs) < 10:
            frame = np.array([
                self.historical_obs[self.time_step],
                self.historical_obs[self.time_step - 1],
                np.zeros([3]),
                np.zeros([3])
            ])
        elif len(self.historical_obs) < 100:
            frame = np.array([
                self.historical_obs[self.time_step],
                self.historical_obs[self.time_step - 1],
                self.historical_obs[self.time_step - 10],
                np.zeros([3])
            ])
        else:
            frame = np.array([
                self.historical_obs[self.time_step],
                self.historical_obs[self.time_step - 1],
                self.historical_obs[self.time_step - 10],
                self.historical_obs[self.time_step - 100],
            ])

        return frame

    def __clearing_house(self, cash_amount=0, security_amount=0):
        current_step = self.data.iloc[self.time_step]

        cash_gained = 0
        security_gained = 0

        if cash_amount > 0:
            # If a security is being purchased the asks is what I care about
            # We want the lowest ask first
            current_asks = [list(map(float, i)) for i in literal_eval(current_step['Asks'])]
            current_asks.sort(key=lambda x: x[0])

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

            depth = 0
            while security_amount > 0:
                if security_amount > current_bids[depth][1]:
                    cash_gained += current_bids[depth][0] * current_bids[depth][1]
                    security_amount -= current_bids[depth][1]
                    depth += 1
                else:
                    cash_gained += security_amount * current_bids[depth][0]
                    security_amount = 0

        return cash_gained, security_gained

    def __take_action(self, action):
        order = action[0]
        percent = action[1]

        # if action_type < 1 then it is of type buy
        if order < 1:
            # Cash value of order is cash on hand * percent
            cash_amount = self.cash * percent
            _, security_gained = self.__clearing_house(cash_amount=cash_amount)

            # Buy trade has cleared so we subtract cash and add security
            self.cash -= cash_amount
            self.security += security_gained

        # if action_type < 2 then it is of type sell
        elif order < 2:
            # Sell amount % of shares held
            security_amount = self.security * percent
            cash_gained, _ = self.__clearing_house(security_amount=security_amount)

            # Sell trade has cleared so we add cash and subtract security
            self.cash += cash_gained
            self.security -= security_amount

        # if action_type > 2 then it is of type hold
        # nothing needs to happen in this case

    def step(self, action):
        # Take an action
        if self.debug:
            print(f'Cash before: {self.cash}')

        self.__take_action(action)

        if self.debug:
            print(f'Action taken was {action}')
            print(f'Cash after: {self.cash}')

        # Move forward in time
        self.time_step += 1

        # Receive reward
        # Reward is cash on hand + cash value of security held
        cash_gained, _ = self.__clearing_house(security_amount=self.security)
        reward = self.cash + cash_gained

        if self.debug:
            print(f'Reward was {reward}')

        done = self.final_step == self.time_step

        obs = self.__next_observation()

        self.historical_behaviour.append([action, reward, obs[0]])

        return obs, reward, done, {}

    def reset(self):
        # Bringing the state of the environment back to initial state
        self.cash = self.starting_cash
        self.security = self.starting_security
        self.historical_obs = []
        self.historical_behaviour = []

        # ToDO: should reset go back to time_step 0 or random step
        self.time_step = 0

        # This will act as the first observation
        return self.__next_observation()

    def render(self, mode='human'):
        # Render the environment to the screen
        print(f'Time step: {self.time_step}')
        print(f'Cash held: {self.cash}')
        print(f'Security held: {self.security}')

        cash_gained, _ = self.__clearing_house(security_amount=self.security)
        net_worth = self.cash + cash_gained

        print(f'Final account balance: {net_worth}')

    def historical(self):
        return self.historical_behaviour
