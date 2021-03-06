from tactile_baselines.common.samplers.base import SampleProcessor
from tactile_baselines.utils import utils
import numpy as np


from pdb import set_trace as st

class ModelSampleProcessor(SampleProcessor):

    def __init__(
                 self,
                 baseline=None,
                 discount=0.99,
                 gae_lambda=1,
                 normalize_adv=True,
                 positive_adv=False,
                 recurrent=False
                 ):

        self.recurrent = recurrent
        self.baseline = baseline
        self.discount = discount
        self.gae_lambda = gae_lambda
        self.normalize_adv = normalize_adv
        self.positive_adv = positive_adv



    def process_samples(self, multiple_trajectories, log=False, log_prefix=''):
        """
        Processes sampled paths. This involves:
        - computing discounted rewards (returns)
        - fitting baseline estimator using the path returns and predicting the return baselines
        - estimating the advantages using GAE (+ advantage normalization id desired)
        - stacking the path data
        - logging statistics of the paths

        Args:
        paths_meta_batch (dict): A list of dict of lists, size: [meta_batch_size] x (batch_size) x [5] x (max_path_length)
        log (boolean): indicates whether to log
        log_prefix (str): prefix for the logging keys

        Returns:
        (list of dicts) : Processed sample data among the meta-batch; size: [meta_batch_size] x [7] x (batch_size x max_path_length)
        """


        samples_data_list, multiple_trajectories = self._compute_samples_data(multiple_trajectories)

        # 8) log statistics if desired
        self._log_path_stats(multiple_trajectories, log=log, log_prefix=log_prefix, trajectory_num=len(multiple_trajectories))
        return samples_data_list


    def _compute_samples_data(self, multiple_trajectories):
        assert type(multiple_trajectories) == list
        if len(multiple_trajectories) > 0:
            assert type(multiple_trajectories[0]) == list
        # 1) compute discounted rewards (returns)
        samples_data_list = []
        for paths in multiple_trajectories:
            for idx, path in enumerate(paths):
                path["returns"] = utils.discount_cumsum(path["rewards"], self.discount)

                # 4) stack path data
            # if self.recurrent:
            #     observations, next_observations, actions, rewards, dones, returns, time_steps, env_infos, agent_infos = self._stack_path_data(paths)
            # else:
            observations, next_observations, actions, rewards, dones, returns, time_steps, env_infos, agent_infos = self._concatenate_path_data(paths)

                # 6) create samples_data object
            samples_data = dict(
                                observations=observations,
                                next_observations=next_observations,
                                actions=actions,
                                rewards=rewards,
                                dones=dones,
                                returns=returns,
                                advantages=returns, # FIXME: Hack for SVG
                                time_steps=time_steps,
                                env_infos=env_infos,
                                agent_infos=agent_infos,
                                )
            samples_data_list.append(samples_data)
        return samples_data_list, multiple_trajectories


    def _concatenate_path_data(self, paths):
        # assert paths[0]["observations"].shape[1] == 1
        observations = np.concatenate([path["observations"] for path in paths])
        next_observations = np.concatenate([np.concatenate([path["observations"][1:], path["observations"][-1][None]]) for path in paths])
        actions = np.concatenate([path["actions"] for path in paths])
        rewards = np.concatenate([path["rewards"] for path in paths])
        dones = np.concatenate([path["dones"].reshape((path["dones"].shape[0])) for path in paths])
        returns = np.concatenate([path["returns"] for path in paths])
        time_steps = np.concatenate([np.arange(path["observations"].shape[0]) for path in paths])
        env_infos = np.array([])
        agent_infos = np.array([])
        # env_infos = utils.concat_tensor_dict_list([path["env_infos"] for path in paths])
        # agent_infos = utils.concat_tensor_dict_list([path["agent_infos"]for path in paths])
        return observations, next_observations, actions, rewards, dones, returns, time_steps, env_infos, agent_infos


    # def _stack_path_data(self, paths):
    #     observations = np.stack([path["observations"] for path in paths])
    #     next_observations = np.stack([np.concatenate([path["observations"][1:], path["observations"][-1][None]])
 # for path in paths])
    #     actions = np.stack([path["actions"] for path in paths])
    #     rewards = np.stack([path["rewards"] for path in paths])
    #     dones = np.stack([path["dones"] for path in paths])
    #     returns = np.stack([path["returns"] for path in paths])
    #     time_steps = np.stack([np.arange(len(path["observations"])) for path in paths])
    #     env_infos = np.array([])
    #     agent_infos = np.array([])
    #     # env_infos = utils.stack_tensor_dict_list([path["env_infos"] for path in paths])
    #     # agent_infos = utils.stack_tensor_dict_list([path["agent_infos"]for path in paths])
    #     return observations, next_observations, actions, rewards, dones, returns, time_steps, env_infos, agent_infos
