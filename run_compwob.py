import sys
import argparse
import logging
import os
import csv
import time
from datetime import datetime

from contextlib import contextmanager

import run_miniwob
from synapse.envs.miniwob.environment import COMPWOB_TASKS

import logging
import urllib3

# urllib3のwarningを抑制
logging.getLogger("urllib3").setLevel(logging.ERROR)


# 単体動作用
# COMPWOB_TASKS = [
    # "click-option_enter-text",
    # "click-button_enter-text",
    # "use-autocomplete_click-dialog",
    # "use-autocomplete_click-dialog-reverse"
# ]

error_tasks = [
    "click-button_enter-text",
]


@contextmanager
def timer(name):
    t0 = time.time()
    yield
    elapsed_time = time.time() - t0

    m = elapsed_time // 60
    s = elapsed_time % 60
    print(f"\n[{name}] done in {m:.0f}:{s:.0f}s\n")


def run(env_name: str, args: dict[str, str]):
    if env_name in error_tasks:
        return False  # pass

    sys.argv = [
        "run_miniwob.py",
        "--env_name", env_name,
        "--model", args["model"],
        "--seed", args["seed"],
        "--num_episodes", args["num_episodes"],
    ]
    succeed = run_miniwob.main()
    return succeed


def run_all_compwob_tasks(args):
    results = {}

    no = 1
    total_no = len(COMPWOB_TASKS)
    for env_name in COMPWOB_TASKS:
        with timer(f"{env_name}"):
            print(f"\n{'=' * 100}\n[{no}/{total_no}] Task: {env_name}")
            no += 1
            succeed = run(env_name, args)
            print(f"succeed: {succeed}")
            results[env_name] = int(succeed)
    return results


def save_results_to_csv(args, compwob_results):
    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    file_name = f"results/compwob_result_{timestamp}.csv"

    with open(file_name, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["compwob results"])

        writer.writerow(["args"])
        for key, value in args.items():
            writer.writerow([key, value])

        writer.writerow([])

        total_succceed = sum(compwob_results.values())
        success_rate = round(total_succceed / len(COMPWOB_TASKS) * 100, 1)
        writer.writerow(["success_rate(%)", success_rate])

        writer.writerow([])

        writer.writerow(["task", "result(1:success, 0:failure)"])
        for key, value in compwob_results.items():
            writer.writerow([key, value])
    print(f"Success: save result to '{file_name}'")


def main():
    args = {
        "model": "gpt-3.5-turbo-1106",
        "seed": "0",
        "num_episodes": "1",
    }

    compwob_results = run_all_compwob_tasks(args)
    save_results_to_csv(args, compwob_results)


if __name__ == "__main__":
    with timer("run_compwob"):
        main()
