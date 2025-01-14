VENV_NAME = .venv
NUM_EPISODES = 1


.PHONY: run_compwob
run_compwob:
	python run_compwob.py


.PHONY: use-autocomplete
use-autocomplete:
	python run_miniwob.py \
		--env_name use-autocomplete \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes $(NUM_EPISODES)


.PHONY: click
click:
	python run_miniwob.py \
		--env_name click-button \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes $(NUM_EPISODES)


.PHONY: comp-click
comp-click:
	python run_miniwob.py \
		--env_name click-option_enter-text \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes $(NUM_EPISODES)


.PHONY: comp-click-rev
comp-click-rev:
	python run_miniwob.py \
		--env_name click-option_enter-text-reverse \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes $(NUM_EPISODES)


.PHONY: comp-login
comp-login:
	python run_miniwob.py \
		--env_name click-option_login-user \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes $(NUM_EPISODES)


.PHONY: comp-login-rev
comp-login-rev:
	python run_miniwob.py \
		--env_name click-option_login-user-reverse \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes $(NUM_EPISODES)


.PHONY: comp-login-transition
comp-login-transition:
	python run_miniwob.py \
		--env_name click-option_login-user-transition \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes $(NUM_EPISODES)


.PHONY: comp-login-transition-rev
comp-login-transition-rev:
	python run_miniwob.py \
		--env_name click-option_login-user-transition-reverse \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes $(NUM_EPISODES)


.PHONY: memory
memory:
	python build_memory.py --env miniwob


.PHONY: memory-comp
memory-comp:
	python build_memory.py --env wm_compwob


.PHONY: t
t:
	python run_miniwob.py \
		--env_name click-button-test \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes 1
