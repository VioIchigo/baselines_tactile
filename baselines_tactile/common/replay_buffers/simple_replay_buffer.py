import numpy as np

from tactile_baselines.utils.serializable import Serializable

from .replay_buffer import ReplayBuffer
from pdb import set_trace as st
import copy


class SimpleReplayBuffer(ReplayBuffer, Serializable):
    def __init__(self, env_spec, max_replay_buffer_size):
        super(SimpleReplayBuffer, self).__init__()
        Serializable.quick_init(self, locals())

        max_replay_buffer_size = int(max_replay_buffer_size)

        self._env_spec = env_spec
        # self._observation_dim = env_spec.observation_space.flat_dim
        # self._action_dim = env_spec.action_space.flat_dim
        self._observation_dim = int(np.prod(env_spec.observation_space.shape))
        self._action_dim = int(np.prod(env_spec.action_space.shape))
        self._max_buffer_size = max_replay_buffer_size
        self._observations = np.zeros((max_replay_buffer_size,
                                       self._observation_dim))
        # It's a bit memory inefficient to save the observations twice,
        # but it makes the code *much* easier since you no longer have to
        # worry about termination conditions.
        self._next_obs = np.zeros((max_replay_buffer_size,
                                   self._observation_dim))
        self._actions = np.zeros((max_replay_buffer_size, self._action_dim))
        self._rewards = np.zeros(max_replay_buffer_size)
        # self._terminals[i] = a terminal was received at time i
        self._terminals = np.zeros(max_replay_buffer_size, dtype='uint8')
        self._advantages = np.zeros(max_replay_buffer_size)
        self._top = 0
        self._size = 0

    def add_sample(self, observation, action, reward, terminal, next_observation, **kwargs):
        self._observations[self._top] = observation.copy()
        self._actions[self._top] = action.copy()
        self._rewards[self._top] = reward.copy()
        self._terminals[self._top] = terminal.copy()
        self._next_obs[self._top] = next_observation.copy()

        self._advance()

    def add_samples(self, observations, actions, rewards, terminals, next_observations, **kwargs):
        assert len(observations) == len(actions) == len(rewards) == len(terminals) == len(next_observations)
        total_num = observations.shape[0]
        observations, actions, rewards, terminals, next_observations = copy.deepcopy([observations,
                                                                                      actions,
                                                                                      rewards,
                                                                                      terminals,
                                                                                      next_observations])
        if self._top + total_num <= self._max_buffer_size:
            self._observations[self._top: self._top + total_num] = observations
            self._actions[self._top: self._top + total_num] = actions
            self._rewards[self._top: self._top + total_num] = rewards
            self._terminals[self._top: self._top + total_num] = terminals
            self._next_obs[self._top: self._top + total_num] = next_observations
        else:
            back_size = self._max_buffer_size - self._top
            redundant = (total_num - back_size) // self._max_buffer_size
            remaining = (total_num - back_size) % self._max_buffer_size
            if redundant == 0:
                self._observations[self._top:] = observations[:back_size]
                self._actions[self._top:] = actions[:back_size]
                self._rewards[self._top:] = rewards[:back_size]
                self._terminals[self._top:] = terminals[:back_size]
                self._next_obs[self._top:] = next_observations[:back_size]

                self._observations[:total_num - back_size] = observations[back_size:]
                self._actions[:total_num - back_size] = actions[back_size:]
                self._rewards[:total_num - back_size] = rewards[back_size:]
                self._terminals[:total_num - back_size] = terminals[back_size:]
                self._next_obs[:total_num - back_size] = next_observations[back_size:]

            else:
                print("WARNING: there are ", redundant * self._max_buffer_size, " samples that are not used. ")
                self._observations[:] = observations[back_size + (redundant - 1) * self._max_buffer_size: back_size + redundant * self._max_buffer_size]
                self._actions[:] = actions[back_size + (redundant - 1) * self._max_buffer_size: back_size + redundant * self._max_buffer_size]
                self._rewards[:] = rewards[back_size + (redundant - 1) * self._max_buffer_size: back_size + redundant * self._max_buffer_size]
                self._terminals[:] = terminals[back_size + (redundant - 1) * self._max_buffer_size: back_size + redundant * self._max_buffer_size]
                self._next_obs[:] = next_observations[back_size + (redundant - 1) * self._max_buffer_size: back_size + redundant * self._max_buffer_size]
                self._observations[:remaining] = observations[back_size + redundant * self._max_buffer_size:]
                self._actions[:remaining] = actions[back_size + redundant * self._max_buffer_size:]
                self._rewards[:remaining] = rewards[back_size + redundant * self._max_buffer_size:]
                self._terminals[:remaining] = terminals[back_size + redundant * self._max_buffer_size:]
                self._next_obs[:remaining] = next_observations[back_size + redundant * self._max_buffer_size:]

        self._advance(num=total_num)

    def add_sample_simple(self, observation, **kwargs):
        self._observations[self._top] = observation
        # self._terminals[self._top] = terminal
        self._advance()

    def add_samples_simple(self, observations, **kwargs):
        total_num = observations.shape[0]
        if self._top + total_num <= self._max_buffer_size:
            self._observations[self._top: self._top + total_num] = observations
            # self._terminals[self._top: self._top + total_num] = terminals
        else:
            back_size = self._max_buffer_size - self._top
            redundant = (total_num - back_size) // self._max_buffer_size
            remaining = (total_num - back_size) % self._max_buffer_size
            if redundant == 0:
                self._observations[self._top:] = observations[:back_size]
                self._observations[:total_num - back_size] = observations[back_size:]
            else:
                print("WARNING: there are ", redundant * self._max_buffer_size, " samples that are not used. ")
                self._observations[:] = observations[back_size + (redundant - 1) * self._max_buffer_size: back_size + redundant * self._max_buffer_size]
                self._observations[:remaining] = observations[back_size + redundant * self._max_buffer_size:]

        self._advance(num=total_num)

    def all_samples(self):
        return self._observations[:self._size], self._actions[:self._size],\
               self._next_obs[:self._size], self._rewards[:self._size], self._terminals[:self._size]

    def terminate_episode(self):
        pass

    def _advance(self, num=1):
        self._top = (self._top + num) % self._max_buffer_size
        if self._size + num < self._max_buffer_size:
            self._size += num
        else:
            self._size = self._max_buffer_size

    def random_batch(self, batch_size, prefix=''):
        indices = np.random.randint(0, self._size, batch_size)
        result = dict()
        result[prefix + 'observations'] = self._observations[indices].copy()
        result[prefix + 'actions'] = self._actions[indices].copy()
        result[prefix + 'rewards'] = self._rewards[indices].copy()
        result[prefix + 'dones'] = self._terminals[indices].copy()
        result[prefix + 'next_observations'] = self._next_obs[indices].copy()
        return result

    def random_batch_simple(self, batch_size, prefix = ''):
        indices = np.random.randint(0, self._size, batch_size)
        result = dict()
        result[prefix + 'observations'] = self._observations[indices].copy()
        return result

    @property
    def size(self):
        return self._size

    def __getstate__(self):
        d = super(SimpleReplayBuffer, self).__getstate__()
        d.update(dict(
            o=self._observations.tobytes(),
            a=self._actions.tobytes(),
            r=self._rewards.tobytes(),
            t=self._terminals.tobytes(),
            no=self._next_obs.tobytes(),
            top=self._top,
            size=self._size,
        ))
        return d

    def __setstate__(self, d):
        super(SimpleReplayBuffer, self).__setstate__(d)
        self._observations = np.fromstring(d['o']).reshape(
            self._max_buffer_size, -1
        )
        self._next_obs = np.fromstring(d['no']).reshape(
            self._max_buffer_size, -1
        )
        self._actions = np.fromstring(d['a']).reshape(self._max_buffer_size, -1)
        self._rewards = np.fromstring(d['r']).reshape(self._max_buffer_size)
        self._terminals = np.fromstring(d['t'], dtype=np.uint8)
        self._top = d['top']
        self._size = d['size']
