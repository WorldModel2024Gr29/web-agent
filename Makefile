VENV_NAME = .venv

all: click


.PHONY: click
click:
	python run_miniwob.py \
		--env_name click-button \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes 1


.PHONY: comp-click
comp-click:
	python run_miniwob.py \
		--env_name click-option_enter-text \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes 1


.PHONY: comp-click-rev
comp-click-rev:
	python run_miniwob.py \
		--env_name click-option_enter-text-reverse \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes 1


.PHONY: comp-login
comp-login:
	python run_miniwob.py \
		--env_name click-option_login-user \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes 1


.PHONY: memory
memory:
	python build_memory.py --env miniwob

.PHONY: t
t:
	python run_miniwob.py \
		--env_name click-button-test \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes 1


.PHONY: activate
activate:
	source .venv/bin/activate
