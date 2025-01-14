import logging
from pathlib import Path
import os
import json
import copy
import re
from selenium.webdriver.common.keys import Keys

from synapse.envs.miniwob.environment import MiniWoBEnv
from synapse.envs.miniwob.action import (
    MiniWoBType,
    MiniWoBElementClickXpath,
    MiniWoBElementClickOption,
    MiniWoBMoveXpath,
)
from synapse.memory.miniwob.build_memory import load_memory, retrieve_exemplar_name
from synapse.utils.llm import (
    generate_response,
    extract_from_response,
    num_tokens_from_messages,
    MAX_TOKENS,
)

from debug import debug_cprint

logger = logging.getLogger(__name__)

ENV_TO_FILTER = [
    "book-flight",
    "click-collapsible-2",
    "click-menu",
    "click-pie",
    "click-shape",
    "click-tab-2",
    "click-tab-2-hard",
    "count-shape",
    "email-inbox",
    "email-inbox-forward-nl",
    "email-inbox-forward-nl-turk",
    "email-inbox-nl-turk",
    "find-word",
    "grid-coordinate",
    "login-user-popup",
    "social-media",
    "social-media-some",
    "terminal",
    "tic-tac-toe",
    "use-autocomplete",
]

from synapse.envs.miniwob.environment import COMPWOB_TASKS

class Agent:
    def __init__(self, args):
        self.args = args
        self.env = MiniWoBEnv(subdomain=args.env_name, headless=args.headless)
        # if any(keyword not in self.args.env_name for keyword in ENV_TO_FILTER):
        if self.args.env_name not in ENV_TO_FILTER:
            self.args.no_filter = True
        if not args.no_memory:
            self.memory = load_memory(args.memory_path)
        self.prompts = None
        self.prompt_type = None
        self.state = None
        self.task = None
        self.done = False
        self.reward = 0
        self.log_path = None
        self.trajectory = None
        self.conversation = None
        self.token_stats = None
        self.demo_traj = []
        # self.rci_limit = 5

    def reset(self, seed: int) -> None:
        self.state = self.env.reset(seed=seed)  # state = osb
        self.task = self.env.get_task()         # env.reset()で初期化したtaskを取得
        self.done = False
        self.reward = 0
        self.trajectory = []
        self.conversation = []
        self.token_stats = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        debug_cprint(f"\nagent.reset()", "yellow")

        exemplar_name = self._get_exemplar_name()
        # exemplar_name = self.args.env_name
        debug_cprint(f" exemplar_name: {exemplar_name}", "red")

        self.log_path = Path(
            os.path.join(
                self.args.log_dir,
                f"{self.args.model}/{self.args.env_name}/{f'no_filt_' if self.args.no_filter and self.args.env_name in ENV_TO_FILTER else ''}{f'no_mem_' if self.args.no_memory else ''}seed_{seed}{'' if exemplar_name == self.args.env_name else f'_{exemplar_name}'}.json",
            )
        )
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        debug_cprint(f" memory_path: {self.args.memory_path}", "yellow")
        with open(os.path.join(self.args.memory_path, "exemplars.json"), "r") as rf:
            exemplar_json = json.load(rf)
            debug_cprint(f" exemplar_json.keys(): \n{exemplar_json.keys()}\n", "yellow")
            debug_cprint(f" exemplar_name in exemplar_json.keys(): {exemplar_name in exemplar_json.keys()}", "yellow")
            # debug_cprint(f" exemplar_json: \n{exemplar_json}\n", "yellow")
            self.prompts = exemplar_json[exemplar_name]
            debug_cprint(f"  prompts: [\n{self.prompts}\n]", "yellow")
        demo = self.prompts["demo"]
        debug_cprint(f"  demo: [\n{demo}\n]", "yellow")

        # set prompt_type
        self.prompt_type = self._get_prompt_type(demo)
        debug_cprint(f" self.prompt_type: {self.prompt_type}", "yellow")

        self.demo_traj = self._get_demo_traj(demo, exemplar_name)
        debug_cprint(f" reset finish\n", "yellow")

    def _get_exemplar_name(self):
        debug_cprint(f" _get_exemplar_name() start", "yellow")
        if self.args.no_memory:
            debug_cprint(f"  no memory", "yellow")
            if self.args.env_name == "click-tab-2-hard":
                exemplar_name = "click-tab-2"
            elif self.args.env_name in [
                "email-inbox",
                "email-inbox-forward-nl",
                "email-inbox-forward-nl-turk",
            ]:
                exemplar_name = "email-inbox-nl-turk"
            else:
                exemplar_name = self.args.env_name
        else:
            if self.args.env_name == "click-button_click-dialog" or self.args.env_name == "click-button_click-dialog-reverse":
                # retrieve_exemplar_nameを呼ぶとclick-butttonのdemoを参照してしまうため、強制的に変更
                exemplar_name = self.args.env_name
            else:
                debug_cprint(f"  has memory", "yellow")
                query = "Task: " + self.task + "\nState:\n" + self.state
                debug_cprint(f"  query: [\n{query}\n]", "yellow")
                exemplar_name = retrieve_exemplar_name(self.memory, query, 3)
        debug_cprint(f" _get_exemplar_name() finish\n", "yellow")
        return exemplar_name

    def _get_prompt_type(self, demo):
        debug_cprint(f" _get_prompt_type() start", "yellow")
        if self.args.no_filter:
            if "trajectory" not in demo[0]:
                prompt_type = "state_act"       # todo: click-button_click-dialog
                assert self.args.env_name != "click-pie"  # context limit
            else:
                prompt_type = "multi_state_act" # todo: click-option_login-user
                assert self.args.env_name != "book-flight"  # context limit
        else:
            if "trajectory" not in demo[0]:
                if "obs" in demo[0]:
                    prompt_type = "obs_act"
                else:  # obs not available due to exemplar mismatch
                    prompt_type = "state_act"
            else:
                prompt_type = "multi_obs_act"   # todo: login-user-popup
        debug_cprint(f" _get_prompt_type() finish\n", "yellow")
        return prompt_type

    def _get_demo_traj(self, demo, exemplar_name):
        debug_cprint(f" _get_traj_demo() start", "yellow")
        demo_traj = []
        if self.prompt_type == "state_act" and "ablation_act_prompt" in self.prompts:
            debug_cprint(f"  1: self.prompt_type == state_act and ablation_act_prompt", "yellow")
            demo_traj.append(
                {"role": "user", "content": self.prompts["ablation_act_prompt"]}
            )
        for d in demo:
            debug_cprint(f"  for d in demo", "yellow")
            if self.prompt_type == "state_act":
                debug_cprint(f"   demo_traj for state_act", "yellow")
                if "state" in d:  # fewer states due to context limit
                    demo_traj.append(
                        {
                            "role": "user",
                            "content": "Observation:\n" + d["state"] + "\nAction:",
                        }
                    )
                    demo_traj.append(
                        {"role": "assistant", "content": "```\n" + d["act"] + "\n```"}
                    )
            elif self.prompt_type == "multi_state_act":
                debug_cprint(f"   demo_traj for multi_state_act", "yellow")
                if exemplar_name in [
                    "login-user-popup",
                    "terminal",
                    "use-autocomplete",
                ]:  # context limit
                    debug_cprint(f"   if exemplar_name in ...", "yellow")
                    if len(demo_traj) > 0:
                        debug_cprint(f"   if len(demo_traj) > 0 -> break", "yellow")
                        break
                if all("state" in t for t in d["trajectory"]):  # fewer states due to context limit
                    debug_cprint(f"   if all(state in t for t in d[trajectory])", "yellow")
                    demo_traj.append(
                        {
                            "role": "user",
                            "content": "Task: " + d["task"] + "\nTrajectory:",
                        }
                    )
                    for t in d["trajectory"]:
                        debug_cprint(f"   for t in d[trajectory])", "yellow")
                        demo_traj.append(
                            {
                                "role": "user",
                                "content": "Observation:\n" + t["state"] + "\nAction:",
                            }
                        )
                        demo_traj.append(
                            {
                                "role": "assistant",
                                "content": "```\n" + t["act"] + "\n```",
                            }
                        )
            elif self.prompt_type == "obs_act":
                debug_cprint(f"   demo_traj for obs_act", "yellow")
                demo_traj.append(
                    {
                        "role": "user",
                        "content": "Observation:\n" + d["obs"] + "\nAction:",
                    }
                )
                demo_traj.append(
                    {"role": "assistant", "content": "```\n" + d["act"] + "\n```"}
                )
            elif self.prompt_type == "multi_obs_act":
                debug_cprint(f"   demo_traj for multi_obs_act", "yellow")
                demo_traj.append(
                    {"role": "user", "content": "Task: " + d["task"] + "\nTrajectory:"}
                )
                for t in d["trajectory"]:
                    demo_traj.append(
                        {
                            "role": "user",
                            "content": "Observation:\n" + t["obs"] + "\nAction:",
                        }
                    )
                    demo_traj.append(
                        {"role": "assistant", "content": "```\n" + t["act"] + "\n```"}
                    )

        _json_demo_traj = json.dumps(demo_traj, indent=4)
        _json_demo_traj = _json_demo_traj.replace("\\n", "\n")
        debug_cprint(f"  demo_traj: [\n{_json_demo_traj}\n]", "yellow")
        debug_cprint(f" _get_traj_demo() finish\n", "yellow")
        return demo_traj


    def _get_query(self, demo):
        debug_cprint(" _get_query() start", "yellow")
        filter_with_code = False
        if self.prompt_type == "obs_act":
            debug_cprint("  self.prompt_type == obs_act", "yellow")
            if "code_filter_prompt" in self.prompts:
                debug_cprint("   code_filter_prompt in self.prompts", "yellow")
                filter_with_code = True
                filter_demo = ""  # create filter demo for possible LLM filtering in case code filtering fails
                for d in demo:
                    if "state" in d:
                        filter_demo += "State:\n" + d["state"] + "\n"
                        filter_demo += "Observation:\n" + d["obs"] + "\n\n"
                query = (
                    self.prompts["code_filter_prompt"]
                    .replace("<task>", self.task)
                    .replace("<state>", self.state)
                )
            elif ("filter_prompt" in self.prompts):  # filter state into obs with specific prompts
                debug_cprint("   filter_prompt in self.prompts", "yellow")
                query = self.prompts["filter_prompt"]
                filter_demo = ""
                for d in demo:
                    if "state" in d:
                        filter_demo += "State:\n" + d["state"] + "\n"
                        filter_demo += "Observation:\n" + d["obs"] + "\n\n"
                query += filter_demo + "State:\n" + self.state + "\nObservation:"
            else:  # filter state into obs
                debug_cprint("   filter state into obs", "yellow")
                filter_demo = ""
                for d in demo:
                    if "state" in d:
                        filter_demo += "State:\n" + d["state"] + "\n"
                        filter_demo += "Observation:\n" + d["obs"] + "\n\n"
                query = filter_demo + "State:\n" + self.state + "\nObservation:"
        else:
            debug_cprint("  self.prompt_type != obs_act", "yellow")
            cur_step = len(self.trajectory)
            if (
                "code_filter_prompt" in self.prompts
                and len(self.prompts["code_filter_prompt"][cur_step]) > 0
            ):
                debug_cprint("   code_filter_prompt in self.prompts", "yellow")
                filter_with_code = True
                filter_demo = ""  # create filter demo for possible LLM filtering in case code filtering fails
                for d in demo:
                    if "state" in d["trajectory"][cur_step]:
                        filter_demo += (
                            "State:\n" + d["trajectory"][cur_step]["state"] + "\n"
                        )
                        filter_demo += (
                            "Observation:\n"
                            + d["trajectory"][cur_step]["obs"]
                            + "\n\n"
                        )
                query = (
                    self.prompts["code_filter_prompt"][cur_step]
                    .replace("<task>", self.task)
                    .replace("<state>", self.state)
                )
            else:
                debug_cprint("   code_filter_prompt not in self.prompts", "yellow")
                filter_demo = ""
                for d in demo:
                    if "state" in d["trajectory"][cur_step]:
                        filter_demo += (
                            "State:\n" + d["trajectory"][cur_step]["state"] + "\n"
                        )
                        filter_demo += (
                            "Observation:\n"
                            + d["trajectory"][cur_step]["obs"]
                            + "\n\n"
                        )
                query = filter_demo + "State:\n" + self.state + "\nObservation:"
        debug_cprint(" _get_query() finish\n", "yellow")
        return query, filter_with_code, filter_demo, cur_step


    def _filter_with_code(self, response, query, filter_demo, cur_step):
        obs_code = extract_from_response(response, "```")
        debug_cprint(f"  obs_code:[{obs_code}]", "yellow")
        try:
            logger.info(f"The code to extract observation:\n{obs_code}")
            namespace = {"state": self.state}
            debug_cprint(f"  exec()", "yellow")
            exec(obs_code, namespace)
            obs = namespace["obs"]
            debug_cprint(f"  exec success", "yellow")
        except Exception as e:
            debug_cprint(f"  exec fail: {e}", "yellow")
            logger.info(
                f"{e}\nFailed to filter the raw state via code generation. Filter with LLM directly"
            )
            if self.prompt_type == "obs_act":
                query = (
                        self.prompts["filter_prompt"]
                        + filter_demo
                        + "State:\n"
                        + self.state
                        + "\nObservation:"
                )
            else:
                query = (
                        self.prompts["filter_prompt"][cur_step]
                        + filter_demo
                        + "State:\n"
                        + self.state
                        + "\nObservation:"
                )
            message = [{"role": "user", "content": query}]
            response, info = generate_response(
                messages=message,
                model=self.args.model,
                temperature=self.args.temperature,
                stop_tokens=["Action:"],
            )
            self.conversation.append(
                {"input": message, "output": response, "token_stats": info}
            )
            for k, v in info.items():
                self.token_stats[k] += v
            obs = response
        return obs


    def _get_obs_by_llm(self, demo):
        debug_cprint(" _get_obs_by_llm() start", "yellow")

        query, filter_with_code, filter_demo, cur_step = self._get_query(demo)
        message = [{"role": "user", "content": query}]
        response, info = generate_response(
            messages=message,
            model=self.args.model,
            temperature=self.args.temperature,
            stop_tokens=["Action:", "Output:", "State:"],
        )
        debug_cprint(f" response: [{response}]", "yellow")

        self.conversation.append(
            {"input": message, "output": response, "token_stats": info}
        )
        for k, v in info.items():
            self.token_stats[k] += v

        if filter_with_code:
            debug_cprint("  filter_with_code", "yellow")
            obs = self._filter_with_code(response, query, filter_demo, cur_step)
        else:
            debug_cprint("  filter: without code", "yellow")
            obs = response

        debug_cprint(" _get_obs_by_llm() finish\n", "yellow")
        return obs


    def filter(self) -> str:
        """
        state abstraction,
        which filters out task-irrelevant information from raw states,
        allowing more exemplars within the limited context
        """
        debug_cprint("\nagent.filter()", "yellow")
        demo = self.prompts["demo"]
        debug_cprint(f" prompt_type: {self.prompt_type}", "yellow")

        # obs = self._get_obs_by_llm(demo)
        # logger.info(f" filtered observation:\n{obs}")
        if self.prompt_type in ["state_act", "multi_state_act"]:
            debug_cprint(" filter: obs = self.state", "yellow")
            obs = self.state
        else:
            debug_cprint(" filter: obs = _get_obs_by_llm()", "yellow")
            obs = self._get_obs_by_llm(demo)
            logger.info(f" filtered observation:\n{obs}")
        debug_cprint(f" obs: [{obs}]", "yellow")
        debug_cprint(f"filter finish\n", "yellow")
        return obs

    def _get_message(self, obs):
        debug_cprint(f" _get_message() start", "yellow")
        sys_message = [{
            "role": "system",
#             "content": """\
# You are a large language model trained to navigate the web.
# Please read the given instructions and observations very carefully.
#
# 1. Reflect on whether you fully understand what is being asked.
#    - If anything is unclear, ask for clarification instead of guessing.
# 2. Formulate a concise plan of action that addresses the exact requirements.
#    - Avoid adding unnecessary details or assumptions.
# 3. Execute your plan by using only the methods (e.g., `agent.type`, `agent.click_xpath`, etc.) available in the Agent class.
# 4. Verify your proposed actions step-by-step to ensure they:
#    - Align precisely with the instructions.
#    - Do not include extra steps unrelated to the instructions.
# 5. If you identify potential ambiguities or conflicts in the instructions, seek clarification before providing final actions.
# 6. Finally, provide your actions succinctly. After listing them, do a brief self-check:
#    - Does each action follow logically from the instructions?
#    - Have you introduced any irrelevant or extraneous actions?
#
# Maintain a high level of confidence in your final response by verifying it carefully. If any doubt remains, request additional information or clarifications.
# """,
            "content": """\
You are a large language model trained to navigate the web. \
To accomplish the task, use methods in the following Agent class to generate actions until you need the new state to proceed.\n```\nclass Agent:\n    def __init__(self, args):\n        ...\n\n    # Action: type a string via the keyboard\n    def type(self, characters: str) -> None:\n        ...\n\n    # Action: click an HTML element with a valid xpath\n    def click_xpath(self, xpath: str):\n        ...\n\n    # Actions: press a key on the keyboard, including:\n    # enter, space, arrowleft, arrowright, backspace, arrowup, arrowdown, command+a, command+c, command+v\n    def press(self, key_type: str) -> None:\n        ...\n\n    # Action: click an option HTML element in a list with a valid xpath\n    def click_option(self, xpath: str):\n        ...\n\n    # Action: move mouse cursor on an HTML element with a valid xpath\n    def movemouse(self, xpath: str):\n        ...\n```
""",
        }]
        query_message = copy.deepcopy(self.demo_traj)
        if self.prompt_type in ["multi_state_act", "multi_obs_act"]:
            debug_cprint(f"  self.prompt_type in ['multi_state_act', 'multi_obs_act']", "yellow")
            query_message.append({
                "role": "user",
                "content": "Task: " + self.task + "\nTrajectory:",
            })
            for t in self.trajectory:
                query_message.append({
                    "role": "user",
                    "content": "Observation:\n" + t["obs"] + "\nAction:",
                })
                query_message.append({
                    "role": "assistant",
                    "content": "```\n" + t["act"] + "\n```"
                })
        query_message.append({
            "role": "user",
            "content": "Observation:\n" + obs + "\nAction:"
        })
        message = sys_message + query_message
        total_num_tokens = num_tokens_from_messages(message, self.args.model)

        _json_message = json.dumps(message, indent=4)
        _json_message = _json_message.replace("\\n", "\n")
        debug_cprint(f"  message: [\n{_json_message}\n]", "yellow")
        debug_cprint(f"  total_num_tokens: {total_num_tokens}", "yellow")

        debug_cprint(f" _get_message() finish\n", "yellow")
        return message, total_num_tokens

    def act(self, obs: str):
        debug_cprint(f"\nagent.act()", "yellow")
        message, total_num_tokens = self._get_message(obs)

        if total_num_tokens > MAX_TOKENS[self.args.model]:
            self.conversation.append({
                "input": message,
                "output": f"FAILED DUE TO THE CONTEXT LIMIT: {total_num_tokens}"
            })
            return None
        response, info = generate_response(
            messages=message,
            model=self.args.model,
            temperature=self.args.temperature,
            stop_tokens=["Observation:"],
        )
        debug_cprint(f" response: [\n{response}\n]", "yellow")
        self.conversation.append({
            "input": message,
            "output": response,
            "token_stats": info
        })
        for k, v in info.items():
            self.token_stats[k] += v
        actions = extract_from_response(response, "```")

        self.trajectory.append({
            "obs": obs,
            "act": actions
        })
        debug_cprint(f" actions: [\n{actions}\n]\n", "yellow")
        return actions

    def step(self, action):
        self.state, reward, self.done, _ = self.env.step(action)
        if self.done:
            self.reward = reward

    def log_results(self):
        # debug_cprint(f"\nlog_results()", "red")
        filename = os.path.splitext(os.path.basename(self.log_path))[0]
        with open(self.log_path, "w") as f:
            json.dump(self.conversation, f, indent=2)
        succeed = self.reward > 0
        if succeed:
            # debug_cprint(f" success", "red")
            new_file_path = self.log_path.with_name(f"{filename}_success.json")
        else:
            # debug_cprint(f" fail", "red")
            new_file_path = self.log_path.with_name(f"{filename}_fail.json")
        if os.path.exists(new_file_path):
            os.remove(new_file_path)
        os.rename(self.log_path, new_file_path)
        return succeed

    # Action: type a string via the keyboard
    def type(self, characters: str) -> None:
        action = MiniWoBType(characters)
        self.step(action)

    def click_xpath(self, xpath: str):
        action = MiniWoBElementClickXpath(xpath)
        self.step(action)

    def press(self, key_type: str) -> None:
        if key_type == "enter":
            action = MiniWoBType("\n")
        elif key_type == "space":
            action = MiniWoBType(" ")
        elif key_type == "arrowleft":
            action = MiniWoBType(Keys.LEFT)
        elif key_type == "arrowright":
            action = MiniWoBType(Keys.RIGHT)
        elif key_type == "backspace":
            action = MiniWoBType(Keys.BACKSPACE)
        elif key_type == "arrowup":
            action = MiniWoBType(Keys.UP)
        elif key_type == "arrowdown":
            action = MiniWoBType(Keys.DOWN)
        elif key_type in ["command+a", "command+c", "command+v"]:
            action = MiniWoBType(key_type)
        else:
            raise ValueError("Invalid instruction")
        self.step(action)

    def click_option(self, xpath: str):
        action = MiniWoBElementClickOption(xpath)
        self.step(action)

    def movemouse(self, xpath: str):
        action = MiniWoBMoveXpath(xpath)
        self.step(action)

    def close(self):
        self.env.close()


"""
You are a large language model trained to navigate the web. 
To accomplish the task, 
use methods in the following Agent class 
to generate actions until you need the new state to proceed.

```
class Agent:
    def __init__(self, args):
        ...

    # Action: type a string via the keyboard
    def type(self, characters: str) -> None:
        ...

    # Action: click an HTML element with a valid xpath
    def click_xpath(self, xpath: str):
        ...

    # Actions: press a key on the keyboard, including:
    # enter, space, arrowleft, arrowright, backspace, arrowup, arrowdown, command+a, command+c, command+v
    def press(self, key_type: str) -> None:
        ...

    # Action: click an option HTML element in a list with a valid xpath
    def click_option(self, xpath: str):
        ...

    # Action: move mouse cursor on an HTML element with a valid xpath
    def movemouse(self, xpath: str):
        ...
```

"""
