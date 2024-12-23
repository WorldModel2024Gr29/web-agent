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


.PHONY: comp-login
comp-login:
	python run_miniwob.py \
		--env_name click-option_login-user-transition \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes 1
