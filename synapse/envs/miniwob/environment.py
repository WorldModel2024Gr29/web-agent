import os

from synapse.envs.miniwob.instance import MiniWoBInstance
from termcolor import cprint

MINIWOB_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "html", "miniwob/"
)

COMPWOB_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "html", "compwob/"
)


EXTRA_HTML_TASKS = [
    "click-dialog",
    "click-dialog-2",
    "use-autocomplete",
    "choose-date",
]

COMPWOB_TASKS = [
    "click-button-sequence_click-checkboxes",
    "click-button-sequence_click-checkboxes-reverse",
    "click-button-sequence_click-option",
    "click-button-sequence_click-option-reverse",
    "click-button-sequence_click-option_login-user",
    "click-button-sequence_click-option_login-user-reverse",
    "click-button-sequence_click-widget_click-link_click-button_click-checkboxes_click-option_click-dialog",
    "click-button-sequence_click-widget_click-link_click-button_click-checkboxes_click-option_click-dialog-reverse",
    "click-button-sequence_click-widget_click-link_click-button_click-checkboxes_click-option_click-dialog_login-user",
    "click-button-sequence_click-widget_click-link_click-button_click-checkboxes_click-option_click-dialog_login-user-reverse",
    "click-button-sequence_login-user-popup",
    "click-button-sequence_login-user-popup-reverse",
    "click-button-sequence_use-autocomplete",
    "click-button-sequence_use-autocomplete-reverse",
    "click-button_click-checkboxes",
    "click-button_click-checkboxes-reverse",
    "click-button_click-checkboxes-transfer",
    "click-button_click-checkboxes-transfer-reverse",
    "click-button_click-dialog",
    "click-button_click-dialog-reverse",
    "click-button_click-link",
    "click-button_click-link-reverse",
    "click-button_click-option",
    "click-button_click-option-reverse",
    "click-button_click-option_login-user",
    "click-button_click-option_login-user-reverse",
    "click-button_click-tab-2-hard",
    "click-button_click-tab-2-hard-reverse",
    # "click-button_enter-text",  # bugged
    "click-checkboxes-soft_enter-password",
    "click-checkboxes-soft_enter-password-reverse",
    "click-checkboxes-soft_multi-layouts",
    "click-checkboxes-soft_multi-layouts-reverse",
    "click-checkboxes-transfer_click-button-sequence_enter-password",
    "click-checkboxes-transfer_click-button-sequence_enter-password-reverse",
    "click-checkboxes-transfer_enter-password_click-dialog",
    "click-checkboxes-transfer_enter-password_click-dialog-reverse",
    "click-checkboxes-transfer_multi-layouts_email-inbox-forward-nl-transition",
    "click-checkboxes-transfer_multi-layouts_email-inbox-forward-nl-transition-reverse",
    "click-checkboxes_click-widget_click-button-sequence",
    "click-checkboxes_click-widget_click-button-sequence-reverse",
    "click-dialog-2_click-widget",
    "click-dialog-2_click-widget-reverse",
    "click-dialog-2_login-user-popup",
    "click-dialog-2_login-user-popup-reverse",
    "click-dialog_click-button-sequence_enter-password",
    "click-dialog_click-button-sequence_enter-password-reverse",
    "click-dialog_click-checkboxes-transfer_click-widget",
    "click-dialog_click-checkboxes-transfer_click-widget-reverse",
    "click-dialog_search-engine",
    "click-dialog_search-engine-reverse",
    "click-link_click-button",
    "click-link_click-button-reverse",
    "click-link_click-button_click-checkboxes_click-dialog",
    "click-link_click-button_click-checkboxes_click-dialog-reverse",
    "click-link_click-button_click-checkboxes_click-option_click-dialog",
    "click-link_click-button_click-checkboxes_click-option_click-dialog-reverse",
    "click-link_click-button_click-dialog",
    "click-link_click-button_click-dialog-reverse",
    "click-link_click-dialog",
    "click-link_click-dialog-reverse",
    "click-link_click-widget",
    "click-link_click-widget-reverse",
    "click-link_enter-text",
    "click-link_enter-text-reverse",
    "click-option_enter-text",
    "click-option_enter-text-reverse",
    "click-option_login-user",
    "click-option_login-user-reverse",
    "click-option_login-user-transition",
    "click-option_login-user-transition-reverse",
    "click-option_multi-layouts_click-widget_login-user-popup-transition",
    "click-option_multi-layouts_click-widget_login-user-popup-transition-reverse",
    "click-option_navigate-tree",
    "click-option_navigate-tree-reverse",
    "click-widget_click-checkboxes-soft",
    "click-widget_click-checkboxes-soft-reverse",
    "click-widget_click-link_click-button_click-checkboxes_click-option_click-dialog",
    "click-widget_click-link_click-button_click-checkboxes_click-option_click-dialog-reverse",
    "click-widget_click-option_click-dialog",
    "click-widget_click-option_click-dialog-reverse",
    "click-widget_enter-password",
    "click-widget_enter-password-reverse",
    "click-widget_multi-layouts",
    "click-widget_multi-layouts-reverse",
    "enter-date_login-user",
    "enter-date_login-user-reverse",
    "enter-password_click-checkboxes_login-user-popup",
    "enter-password_click-checkboxes_login-user-popup-reverse",
    "enter-password_click-option",
    "enter-password_click-option-reverse",
    "login-user-popup_email-inbox-forward-nl-turk-transition",
    "login-user-popup_email-inbox-forward-nl-turk-transition-reverse",
    "login-user_navigate-tree",
    "login-user_navigate-tree-reverse",
    "login-user_navigate-tree-transition",
    "login-user_navigate-tree-transition-reverse",
    "multi-layouts_login-user",
    "multi-layouts_login-user-reverse",
    "use-autocomplete_click-dialog",
    "use-autocomplete_click-dialog-reverse",
]


class MiniWoBEnv(object):
    def __init__(
        self,
        subdomain: str,
        headless: bool = False,
    ):
        """Creates a new MiniWoBEnv with no instances.
        Must call configure() to set up instances.

        Args:
            subdomain (str): MiniWoB task name (e.g., "click-test")
            headless (bool): Whether to render GUI
        """
        self.subdomain = subdomain
        self.instance = None
        self.headless = headless
        self.task = None

    def configure(self, seed: int = None, **kwargs):
        """Creates the required number of MiniWoBInstance.

        Args:
            seed (int): Random seed to set the instance;

        kwargs are passed into the constructor of MiniWoBInstance:
            headless (bool): Whether to render GUI
            base_url (str): Base URL, which is usually one of the following
                - http://localhost:8000/     (served by http-serve)
                - file:///path/to/miniwob-plusplus/html/
            cache_state (bool): Whether to cache and return the initial
                state; only make sense if the task interface never changes
            threading (bool): Whether to run the instances in separate threads
            reward_processor (callable; optional): A function that takes
                the metadata and return a reward (see miniwob.reward)
            seeds (list[object]): Random seeds to set for each instance;
                len(seeds) must be equal to num_instances.
            wait_ms (float): Pause the instance after each action for this
                amount of time (in milliseconds).
            block_on_reset (bool): On reset, block until the page loads.
            refresh_freq (int): Every this number of episodes,
                refresh the page at the beginning of the next episode.
                Takes time but cleans up any lingering states and memory leaks.
                *** Must specify `seeds` at each reset call.
            initial_mode (str): Initial data mode (e.g., "train", "test")
        """
        assert seed is not None, "seed must be specified"
        if self.instance is not None:
            self.instance.close()
        self.instance = None
        self.instance = MiniWoBInstance(
            index=0,
            subdomain=self.subdomain,
            seed=seed,
            headless=self.headless,
            base_url=f"file://{COMPWOB_DIR if self.subdomain in COMPWOB_TASKS else MINIWOB_DIR}",
            wait_ms=1000.0,
            refresh_freq=1,
            **kwargs,
        )
        self.instance.start()
        self.instance.wait()

    def reset(
        self,
        seed: int = None,
        record_screenshots: bool = False,
    ) -> str:
        """Forces stop and start all instances.

        Args:
            seed (int): Random seed to set the instance
            record_screenshots (bool): Whether to record screenshots of the states.
        Returns:
            obs (str)
        """
        cprint(f"env.reset()", "blue")

        self.configure(seed=seed)
        self.set_record_screenshots(record_screenshots)

        states = [None]
        # cprint(f" states before instance.call: \n[{states}]", "blue")
        cprint(f"  instance.call()", "blue")
        self.instance.call(self.instance.reset, states, seed)  # HTML取得
        cprint(f"  instance.wait()", "blue")
        self.instance.wait()

        cprint(f" states after instance.call : \n[{states}]", "blue")
        cprint(f"   len(states) : {len(states)}", "blue")
        cprint(f"   states[0].html_body : \n[{states[0].html_body}]", "blue")
        cprint(f"   states[0].html_extra : \n[{states[0].html_extra}]", "blue")

        cprint(f" obs = self.state2html(states)", "blue")
        obs = self.state2html(states)
        cprint(f" obs: [\n{obs}\n]", "blue")

        self.task = states[0].utterance

        # DOMからQueryを抽出？
        cprint(f" task: {self.task}\n", "blue")
        return obs

    def step(self, action):
        """Applies an action on each instance and returns the results.

        Args:
            action (MiniWoBAction)

        Returns:
            state (MiniWoBState)
            reward (float)
            done (bool)
            info (dict)
        """
        states = [None]
        rewards = [-1.0]
        dones = [True]
        info = {"n": [{}]}
        self.instance.call(
            self.instance.step, action, states, rewards, dones, info["n"]
        )
        self.instance.wait()
        obs = self.state2html(states)

        return obs, rewards[0], dones[0], info["n"][0]

    def set_record_screenshots(self, record_screenshots):
        """Adjust whether the record the screenshots of the states.

        Args:
            record_screenshots (bool)
        """
        self.instance.record_screenshots = record_screenshots

    def close(self):
        self.instance.call(self.instance.close)
        self.instance.wait()

    def get_task(self):
        return self.task

    def state2html(self, states: list) -> str:
        if states[0] is not None:
            obs = states[0].html_body
            if self.subdomain in EXTRA_HTML_TASKS:
                obs += states[0].html_extra
        else:
            obs = None

        return obs
