import argparse
import logging
import os

from synapse.agents.miniwob import Agent

logger = logging.getLogger("synapse")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.propagate = False


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_episodes", type=int, default=1)
    parser.add_argument("--env_name", type=str)
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo-0301")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--headless", action="store_true", default=False)
    parser.add_argument("--no_filter", action="store_true", default=False)
    parser.add_argument("--no_memory", action="store_true", default=False)

    return parser


def is_wm_compwob_task(env_name: str):
    from synapse.memory.wm_compwob.build_memory import EXEMPLAR_LIST
    return env_name in EXEMPLAR_LIST


def main():
    try:
        parser = create_parser()
        args = parser.parse_args()

        current_path = os.getcwd()
        # if is_wm_compwob_task(args.env_name):
        #     print(f"env is wm_compwob task")
        #     memory_path = "synapse/memory/wm_compwob"
        #     log_dir = "results/wm_compwob"
        # else:
        #     print(f"env is miniwob task")
        #     memory_path = "synapse/memory/miniwob"
        #     log_dir = "results/miniwob"

        memory_path = "synapse/memory/miniwob"
        log_dir = "results/miniwob"

        args.memory_path = os.path.join(current_path, memory_path)
        args.log_dir = os.path.join(current_path, log_dir)

        agent = Agent(args=args)
        if args.env_name in ["book-flight", "terminal", "use-autocomplete"]:
            max_steps = 2
        elif args.env_name in ["login-user", "login-user-popup"]:
        # elif args.env_name in ["login-user", "login-user-popup", "click-option_enter-text"]:
            max_steps = 3
        elif args.env_name in ["guess-number", "tic-tac-toe"]:
            max_steps = 10
        else:
            max_steps = 1

        for i in range(args.num_episodes):
            # reset
            agent.reset(seed=args.seed + i)

            for _ in range(max_steps):
                # filter
                obs = agent.filter()

                # action
                actions = agent.act(obs)
                if actions is None:
                    break
                try:
                    logger.info(f"Actions:\n{actions}")
                    exec(actions)
                except:
                    logger.info(f"Failed to execute action. Try again.")
                if agent.done:
                    break
            agent.log_results()
        agent.close()

    except Exception as e:
        print(f"Fatal error: {str(e)}")
        print("Traceback:")
        _tb = e.__traceback__
        while _tb is not None:
            _filename = _tb.tb_frame.f_code.co_filename
            _line_number = _tb.tb_lineno
            print(f"File '{_filename}', line {_line_number}")
            _tb = _tb.tb_next
        print(f"Error: {str(e)}")

        print(f"\nagent.close()")
        agent.close()

        sys.exit(1)


if __name__ == "__main__":
    main()
