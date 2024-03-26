import numpy as np
from gymnasium.utils import EzPickle

from pettingzoo.mpe._mpe_utils.core import Agent, Landmark, World
from pettingzoo.mpe._mpe_utils.scenario import BaseScenario
from pettingzoo.mpe._mpe_utils.simple_env import SimpleEnv, make_env
from pettingzoo.utils.conversions import parallel_wrapper_fn


class raw_env(SimpleEnv, EzPickle):
    def __init__(self, max_cycles=25, continuous_actions=False, render_mode=None):
        EzPickle.__init__(
            self,
            max_cycles=max_cycles,
            continuous_actions=continuous_actions,
            render_mode=render_mode,
        )
        scenario = Scenario()
        world = scenario.make_world()
        SimpleEnv.__init__(
            self,
            scenario=scenario,
            world=world,
            render_mode=render_mode,
            max_cycles=max_cycles,
            continuous_actions=continuous_actions,
        )
        self.metadata["name"] = "my_simple_push_v3"


env = make_env(raw_env)
parallel_env = parallel_wrapper_fn(env)


class Scenario(BaseScenario):
    def make_world(self):
        world = World()
        # set any world properties first
        world.dim_c = 2
        num_agents = 1
        num_adversaries = 1
        num_landmarks = 2
        # add agents
        world.agents = [Agent() for i in range(num_agents)]
        for i, agent in enumerate(world.agents):
            agent.adversary = True if i < num_adversaries else False
            base_name = "adversary" if agent.adversary else "agent"
            base_index = i if i < num_adversaries else i - num_adversaries
            agent.name = f"{base_name}_{base_index}"
            agent.collide = True
            agent.silent = True
        # add landmarks
        world.landmarks = [Landmark() for i in range(num_landmarks)]
        for i, landmark in enumerate(world.landmarks):
            landmark.name = "landmark %d" % i
            landmark.collide = False
            landmark.movable = False
        return world

    def reset_world(self, world, np_random):
        # random properties for landmarks
        for i, landmark in enumerate(world.landmarks):
            landmark.color = np.array([0.1, 0.1, 0.1])
            landmark.color[i + 1] += 0.8
            landmark.index = i
        # set goal landmark
        goal = np_random.choice(world.landmarks)
        for i, agent in enumerate(world.agents):
            # agent.goal_a = goal
            agent.color = np.array([0.25, 0.25, 0.25])
            if agent.adversary:
                agent.color = np.array([0.75, 0.25, 0.25])
            else:
                # j = goal.index
                agent.color += np.array([0.25, 0.25, 0.0])
        # set random initial states
        for agent in world.agents:
            agent.state.p_pos = np_random.uniform(-1, +1, world.dim_p)
            agent.state.p_vel = np.zeros(world.dim_p)
            agent.state.c = np.zeros(world.dim_c)
        for i, landmark in enumerate(world.landmarks):
            landmark.state.p_pos = np_random.uniform(-1, +1, world.dim_p)
            landmark.state.p_vel = np.zeros(world.dim_p)

    def reward(self, agent, world):
        # Agents are rewarded based on minimum agent distance to each landmark
        return (
            self.adversary_reward(agent, world)
            if agent.adversary
            else self.agent_reward(agent, world)
        )

    def agent_reward(self, agent, world):
        # the distance to the goal
        # return -np.sqrt(np.sum(np.square(agent.state.p_pos - agent.goal_a.state.p_pos)))

        # both landmarks touched
        # dists_to_landmarks = [np.sqrt(np.sum(np.square(agent.state.p_pos - landmark.state.p_pos))) for landmark in world.landmarks]
        # touched_landmarks = sum(dist <= 0.1 for dist in dists_to_landmarks)  # Assuming a touch threshold of 0.1
        # # Full reward if touched both, partial or none otherwise
        # return 1.0 if touched_landmarks == len(world.landmarks) else 0.0
        return 0

    def adversary_reward(self, agent, world):
        # old reward

        # keep the nearest good agents away from the goal
        # agent_dist = [
        #     np.sqrt(np.sum(np.square(a.state.p_pos - a.goal_a.state.p_pos)))
        #     for a in world.agents
        #     if not a.adversary
        # ]
        # pos_rew = min(agent_dist)
        # # nearest_agent = world.good_agents[np.argmin(agent_dist)]
        # # neg_rew = np.sqrt(np.sum(np.square(nearest_agent.state.p_pos - agent.state.p_pos)))
        # neg_rew = np.sqrt(
        #     np.sum(np.square(agent.goal_a.state.p_pos - agent.state.p_pos))
        # )
        # # neg_rew = sum([np.sqrt(np.sum(np.square(a.state.p_pos - agent.state.p_pos))) for a in world.good_agents])
        # return pos_rew - neg_rew

        # new - prevent good agent from touching

        # good_agent = next(a for a in world.agents if not a.adversary)
        # dists_to_landmarks = [np.sqrt(np.sum(np.square(good_agent.state.p_pos - landmark.state.p_pos))) for landmark in world.landmarks]
        # touched_landmarks = sum(dist <= 0.1 for dist in dists_to_landmarks)
        # return 1.0 if touched_landmarks < len(world.landmarks) else -1.0

        return 0
    
    def observation(self, agent, world):
        # get positions of all entities in this agent's reference frame
        entity_pos = []
        for entity in world.landmarks:  # world.entities:
            entity_pos.append(entity.state.p_pos - agent.state.p_pos)
        # entity colors
        entity_color = []
        for entity in world.landmarks:  # world.entities:
            entity_color.append(entity.color)
        # communication of all other agents
        comm = []
        other_pos = []
        for other in world.agents:
            if other is agent:
                continue
            comm.append(other.state.c)
            other_pos.append(other.state.p_pos - agent.state.p_pos)
        if not agent.adversary:
            return np.concatenate(
                [agent.state.p_vel]
                + [agent.goal_a.state.p_pos - agent.state.p_pos]
                + [agent.color]
                + entity_pos
                + entity_color
                + other_pos
            )
        else:
            return np.concatenate([agent.state.p_vel] + entity_pos + other_pos)