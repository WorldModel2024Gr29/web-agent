run-gpt-3.5:
	python run_miniwob.py \
		--env_name click-button \
		--model gpt-3.5-turbo-1106 \
		--seed 0 \
		--num_episodes 1

run-gpt-4:
	python run_miniwob.py \
		--env_name click-button \
		--model gpt-4-0613 \
		--seed 0 \
		--num_episodes 1