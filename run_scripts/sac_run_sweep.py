import os
import json
import tensorflow as tf
import numpy as np
INSTANCE_TYPE = 'c4.xlarge'
EXP_NAME = 'mujoco'


from experiment_utils.run_sweep import run_sweep
from tactile_baselines.sac.sac import SAC
from tactile_baselines.utils.utils import set_seed, ClassEncoder
from envs import gym
from pdb import set_trace as st
from tactile_baselines.sac.sac_trainer import Trainer
from tactile_baselines.common.samplers.base import BaseSampler
from tactile_baselines.common.samplers.mb_sample_processor import ModelSampleProcessor
from tactile_baselines.common.policies.gaussian_mlp_policy import GaussianMLPPolicy
from tactile_baselines import logger
from tactile_baselines.common.value_functions.value_function import ValueFunction
from tactile_baselines.common.baselines.linear_baseline import LinearFeatureBaseline
from tactile_baselines.common.cmd_util import common_arg_parser, parse_unknown_args, make_vec_env, make_env
from run_scripts.her_run_sweep import build_env


def run_experiment(**kwargs):
    exp_dir = os.getcwd() + '/data/' + EXP_NAME
    logger.configure(dir=exp_dir, format_strs=['stdout', 'log', 'csv'], snapshot_mode='last')
    json.dump(kwargs, open(exp_dir + '/params.json', 'w'), indent=2, sort_keys=True, cls=ClassEncoder)
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    config.gpu_options.per_process_gpu_memory_fraction = kwargs.get('gpu_frac', 0.95)
    sess = tf.Session(config=config)
    with sess.as_default() as sess:

        # Instantiate classes
        set_seed(kwargs['seed'])

        baseline = kwargs['baseline']()

#        env = normalize(kwargs['env']())
        arg_list = []
        for key in kwargs.keys():
            arg_list.append('--' + key)
            arg_list.append(str(kwargs[key]))
        arg_parser = common_arg_parser()
        args, unknown_args = arg_parser.parse_known_args(arg_list)
        env = build_env(args)

        Qs = [ValueFunction(name="q_fun_%d" % i,
                            obs_dim=int(np.prod(env.observation_space.shape)),
                            action_dim=int(np.prod(env.action_space.shape)),
                            hidden_nonlinearity=kwargs['vfun_hidden_nonlineariy'],
                            ) for i in range(2)]

        Q_targets = [ValueFunction(name="q_fun_target_%d" % i,
                                   obs_dim=int(np.prod(env.observation_space.shape)),
                                   action_dim=int(np.prod(env.action_space.shape)),
                                   hidden_nonlinearity=kwargs['vfun_hidden_nonlineariy'],
                                   ) for i in range(2)]

        policy = GaussianMLPPolicy(
            name="policy",
            obs_dim=np.prod(env.observation_space.shape),
            action_dim=np.prod(env.action_space.shape),
            hidden_sizes=kwargs['policy_hidden_sizes'],
            learn_std=kwargs['policy_learn_std'],
            output_nonlinearity=kwargs['policy_output_nonlinearity'],
            hidden_nonlinearity=kwargs['policy_hidden_nonlinearity'],
            squashed=True
        )

        sampler = BaseSampler(
            env=env,
            policy=policy,
            num_rollouts=kwargs['num_rollouts'],
            max_path_length=kwargs['max_path_length'],

        )

        sample_processor = ModelSampleProcessor(
            baseline=baseline,
            discount=kwargs['discount'],
        )

        algo = SAC(
            policy=policy,
            discount=kwargs['discount'],
            learning_rate=kwargs['learning_rate'],
            env=env,
            Qs=Qs,
            Q_targets=Q_targets,
            reward_scale=kwargs['reward_scale'],
            batch_size=kwargs['batch_size']
        )

        trainer = Trainer(
            algo=algo,
            policy=policy,
            env=env,
            sampler=sampler,
            sample_processor=sample_processor,
            n_itr=kwargs['n_itr'],
            sess=sess,
        )

        trainer.train()
    sess.__exit__()


if __name__ == '__main__':
    sweep_params = {
        'algo': ['sac'],
        'seed': [2],
        'baseline': [LinearFeatureBaseline],
        'env': ['HalfCheetah-v3'],
#        'env': [HalfCheetahEnv],

        # Policy
        'policy_hidden_sizes': [(256, 256)],
        'policy_learn_std': [True],
        'policy_output_nonlinearity': [None],
        'policy_hidden_nonlinearity': ['relu'],

        # Value Function
        'vfun_hidden_nonlineariy': ['relu'],


        # Env Sampling
        'num_rollouts': [1],
        'n_parallel': [1],

        # Problem Conf
        'n_itr': [3000],
        'max_path_length': [1000],
        'discount': [0.99],
        'learning_rate': [3e-4],
        'reward_scale': [1.],
        'batch_size': [256],
        }

    run_sweep(run_experiment, sweep_params, EXP_NAME, INSTANCE_TYPE)
