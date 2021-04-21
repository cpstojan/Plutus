from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines.common.vec_env import SubprocVecEnv
from stable_baselines import PPO2
from stable_baselines import TRPO

import ExchangeEnv

# When using SubprocVecEnv, users must wrap the code in an if __name__ == "__main__"
if __name__ == '__main__':
    # The algorithms require a vectorized environment to run
    env_train = SubprocVecEnv([lambda: ExchangeEnv.ExchangeEnv(r"C:\Users\chris\OneDrive\Documents\GitHub\Data\Cumulative\Train",
                                                               10000, 0)])

    # In the paper a policy with a feed forward network with two hidden layers each consisting of 64 neurons was used
    policy_kwargs = dict(net_arch=[64, 64])

    # From the paper:
    #   Lambda = 0.95
    #   Clipping parameter = 0.2
    #   cvf = 0.5
    #   cH = 0.01
    #   Adam minibatch = 4
    #   Learning rate = 0.00025
    #   Trained over 10,000,000 time steps
    model = PPO2(policy=MlpPolicy, env=env_train, policy_kwargs=policy_kwargs, lam=0.95, cliprange=0.2, vf_coef=0.5,
                 ent_coef=0.01, nminibatches=4, learning_rate=0.00025, verbose=1)

    model.learn(total_timesteps=10000000)
    model.save('ppo2_trader')

    # Using a different environment to test the model
    env_test = SubprocVecEnv([lambda: ExchangeEnv.ExchangeEnv(r"C:\Users\chris\OneDrive\Documents\GitHub\Data\Cumulative\Test",
                                                              10000, 0)])
    obs = env_test.reset()
    done = False

    while not done:
        action, _states = model.predict(obs)
        obs, rewards, done, info = env_test.step(action)
        print(action)
        # print(env_test.env_method("historical"))
