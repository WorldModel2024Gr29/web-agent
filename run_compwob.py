import sys
import argparse
import logging
import os
import csv
import time
from datetime import datetime

from contextlib import contextmanager
from typing import Any
from termcolor import cprint

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
            cprint(f"succeed: {succeed}", "green" if succeed else "red")
            results[env_name] = int(succeed)

    return results


def _write_args(writer: Any, args: dict[str, str]) -> None:
    writer.writerow(["args"])
    for key, value in args.items():
        writer.writerow([key, value])


def _write_success_rate(writer: Any, compwob_results: dict) -> None:
    """
    forward-task, reversed-task の成功率、全タスクの成功率をcsvに書き込む
    """
    writer.writerow(["success rate"])

    forward_task_count = 0
    forward_task_succeed_count = 0
    reversed_task_count = 0
    reversed_task_succeed_count = 0

    for task, result in compwob_results.items():
        if task.endswith("-reverse"):
            reversed_task_count += 1
            reversed_task_succeed_count += result
        else:
            forward_task_count += 1
            forward_task_succeed_count += result

    # forward-task success rate
    forward_task_success_rate = round(0 if forward_task_count == 0 else forward_task_succeed_count / forward_task_count * 100, 1)
    writer.writerow(["forward-task success rate(%)", forward_task_success_rate])

    # reversed-task success rate
    reversed_task_success_rate = round(0 if reversed_task_count == 0 else reversed_task_succeed_count / reversed_task_count * 100, 1)
    writer.writerow(["reversed-task success rate(%)", reversed_task_success_rate])

    # total success_rate
    total_task_succceed = forward_task_succeed_count + reversed_task_succeed_count
    total_task_count = forward_task_count + reversed_task_count
    total_task_success_rate = round(0 if total_task_count else total_task_succceed / total_task_count * 100, 1)
    writer.writerow(["total success rate(%)", total_task_success_rate])


def _write_task_results(writer: Any, compwob_results: dict) -> None:
    writer.writerow(["task", "result(1:success, 0:failure)"])
    for key, value in compwob_results.items():
        writer.writerow([key, value])


def _write_empty_line(writer: Any) -> None:
    writer.writerow([])


def save_results_to_csv(args, compwob_results):
    directory = "results/compwob"
    if not os.path.exists(directory):
        os.makedirs(directory)

    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    file_name = f"{directory}/compwob_result_{timestamp}.csv"

    with open(file_name, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["compwob results"])

        _write_args(writer, args)
        _write_empty_line(writer)
        _write_success_rate(writer, compwob_results)
        _write_empty_line(writer)
        _write_task_results(writer, compwob_results)

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
