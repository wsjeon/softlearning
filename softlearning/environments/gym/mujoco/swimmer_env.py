import numpy as np
from gym.envs.mujoco import mujoco_env
from gym import utils


class SwimmerEnv(mujoco_env.MujocoEnv, utils.EzPickle):
    def __init__(self,
                 forward_reward_weight=1.0,
                 ctrl_cost_weight=1e-4,
                 exclude_current_positions_from_observation=True):
        self._forward_reward_weight = forward_reward_weight
        self._ctrl_cost_weight = ctrl_cost_weight
        self._exclude_current_positions_from_observation = (
            exclude_current_positions_from_observation)

        mujoco_env.MujocoEnv.__init__(self, 'swimmer.xml', 4)
        utils.EzPickle.__init__(
            self,
            forward_reward_weight=self._forward_reward_weight,
            ctrl_cost_weight=self._ctrl_cost_weight,
            exclude_current_positions_from_observation=(
                self._exclude_current_positions_from_observation))

    def control_cost(self, action):
        control_cost = self._ctrl_cost_weight * np.sum(np.square(action))
        return control_cost

    def step(self, action):
        x_position_before = self.sim.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        x_position_after = self.sim.data.qpos[0]

        x_velocity = ((x_position_after - x_position_before)
                      / self.dt)
        forward_reward = self._forward_reward_weight * x_velocity

        ctrl_cost = self.control_cost(action)

        xy_positions = self.sim.data.qpos[0:2]

        observation = self._get_obs()
        reward = forward_reward - ctrl_cost
        done = False
        info = {
            'x_position': xy_positions[0],
            'y_position': xy_positions[1],
            'xy_position': np.linalg.norm(xy_positions, ord=2),

            'x_velocity': x_velocity,
            'forward_reward': forward_reward,
        }

        return observation, reward, done, info

    def _get_obs(self):
        position = self.sim.data.qpos.flat.copy()
        velocity = self.sim.data.qvel.flat.copy()

        if self._exclude_current_positions_from_observation:
            position = position[2:]

        observation = np.concatenate([position, velocity]).ravel()
        return observation

    def reset_model(self):
        c = 0.1
        qpos = self.init_qpos + self.np_random.uniform(
            low=-c, high=c, size=self.model.nq)
        qvel = self.init_qvel + self.np_random.uniform(
            low=-c, high=c, size=self.model.nv)

        self.set_state(qpos, qvel)

        observation = self._get_obs()
        return observation
