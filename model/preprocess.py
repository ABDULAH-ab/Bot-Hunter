# import os
# # order="python preprocess_features.py"
# # os.system(order)
# order="python prepshould rocess_text.py"
# os.system(order)
# order="python preprocess_relations.py"
# os.system(order)

import subprocess
import sys
import os


def run_step(script_name):
	print(f"Running {script_name}...")
	subprocess.run([sys.executable, script_name], check=True)
	print(f"Finished {script_name}")


if __name__ == "__main__":
	# Force-set env vars (don't use setdefault — stale values from previous sessions persist)
	os.environ["BATCH_SIZE"] = os.environ.get("BATCH_SIZE_OVERRIDE", "8")	# RTX 3090 can handle 8
	os.environ["MAX_TWEETS_PER_USER"] = "20"	# Paper config
	os.environ["TEXT_MODEL"] = "vinai/bertweet-base"	# Twitter-specific
	os.environ["FORCE_REBUILD"] = "0"
	
	# Disable HF warnings
	os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
	os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")
	
	print(
		"Config -> "
		f"BATCH_SIZE={os.environ['BATCH_SIZE']}, "
		f"MAX_TWEETS_PER_USER={os.environ['MAX_TWEETS_PER_USER']}, "
		f"TEXT_MODEL={os.environ['TEXT_MODEL']}"
	)

	# Run the full preprocessing pipeline
	run_step("preprocess_features.py")
	run_step("preprocess_tweet_features.py")
	run_step("preprocess_text.py")
	run_step("preprocess_relations.py")