from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import PPO2

import ExchangeEnv


# The algorithms require a vectorized environment to run
env = DummyVecEnv([lambda: ExchangeEnv.ExchangeEnv(r"C:\Users\chris\OneDrive\Documents\GitHub\Plutus\data", 1000, 0)])

model = PPO2(MlpPolicy, env, verbose=1)
model.learn(total_timesteps=50000)

obs = env.reset()
for i in range(400):
    action, _states = model.predict(obs)
    obs, rewards, done, info = env.step(action)
    env.render()
