from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import PPO2
from stable_baselines import TRPO

import ExchangeEnv


# The algorithms require a vectorized environment to run
env = DummyVecEnv([lambda: ExchangeEnv.ExchangeEnv(r"C:\Users\chris\Downloads\drive-download-20210409T040911Z-001", 10000, 0)])

# model = PPO2(MlpPolicy, env, verbose=1)
model = TRPO(MlpPolicy, env, verbose=1)
model.learn(total_timesteps=12500000)

obs = env.reset()
done = False

while not done:
    action, _states = model.predict(obs)
    print(action)
    obs, rewards, done, info = env.step(action)
    env.render()