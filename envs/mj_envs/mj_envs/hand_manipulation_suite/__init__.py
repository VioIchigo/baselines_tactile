from envs.gym.envs.registration import register
from envs.mj_envs.mj_envs.mujoco_env import MujocoEnv

# Swing the door open
register(
    id='door-v0',
    entry_point='envs.mj_envs.mj_envs.hand_manipulation_suite:DoorEnvV0',
    max_episode_steps=200,
)
from envs.mj_envs.mj_envs.hand_manipulation_suite.door_v0 import DoorEnvV0

# Hammer a nail into the board
register(
    id='hammer-v0',
    entry_point='envs.mj_envs.mj_envs.hand_manipulation_suite:HammerEnvV0',
    max_episode_steps=200,
)
from envs.mj_envs.mj_envs.hand_manipulation_suite.hammer_v0 import HammerEnvV0

# Reposition a pen in hand
register(
    id='pen-v0',
    entry_point='envs.mj_envs.mj_envs.hand_manipulation_suite:PenEnvV0',
    max_episode_steps=200,
)
from envs.mj_envs.mj_envs.hand_manipulation_suite.pen_v0 import PenEnvV0

# Relcoate an object to the target
register(
    id='relocate-v0',
    entry_point='envs.mj_envs.mj_envs.hand_manipulation_suite:RelocateEnvV0',
    max_episode_steps=200,
)
from envs.mj_envs.mj_envs.hand_manipulation_suite.relocate_v0 import RelocateEnvV0

# Relcoate an object to the target
register(
    id='pusher-v0',
    entry_point='envs.mj_envs.mj_envs.hand_manipulation_suite:PusherPlaneStraightEnv',
    max_episode_steps=200,
)
from envs.mj_envs.mj_envs.hand_manipulation_suite.pusherplanestraight_v0 import PusherPlaneStraightEnv
from envs.mj_envs.mj_envs.hand_manipulation_suite.pusherplanestraight_v0 import PusherStraight