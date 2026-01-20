### General

This repository contains benchmark instances derived from a real-world biomanufacturing factory. The instances are designed to reflect practical scheduling constraints and operational complexity encountered in industrial biomanufacturing environments, making them suitable for both research and applied optimization studies.

The benchmark instances are supported by PyJobShop, a constraint programming–based interface for modeling and solving scheduling problems. PyJobShop provides a unified modeling layer with backends for Google OR-Tools and IBM ILOG CP Optimizer. Please note that using CP Optimizer requires a valid commercial license.

Together, this setup enables reproducible benchmarking and comparison of constraint programming approaches on realistic biomanufacturing scheduling problems.


### Installation with uv (after cloning or forking the repository)

We make use of uv (https://github.com/astral-sh/uv) for the installation and testing.

`cd decision-focused-learning-codebase`

`uv sync --all-extras --all-groups`

`uv run pytest`

### Before committing / pushing

We make use of pre-commit (https://pre-commit.com/) for formatting of our files.

`uv run pre-commit install`

`uv run pre-commit run --all-files`

### Running experiments on DelftBlue

We make use of the benchmark_instance.py and the jobscript.py to submit jobs to DelftBlue for each instance configuration
combination. \

To only print the batch jobs you can run the following command:

`uv run submit.py --config "config.json" --dry-run`

To actually submit the jobs you can run the following command and add the configuration in a config.json:

`uv run submit.py --config "config.json"`

To solve all the instances from the directory specified in the config file, you can run the following command:

`uv run submit.py --config "config.json" --solve-dir`

To commit and push the new summary files from server (DelftBlue) to the git, do the following:

`git add ./summaries`

`git commit -m "Add/update summaries"`

`git push origin main`

To summarize the results that come from one config, you can run the following command (check which path you need):

`uv run summarize_results.py --dir "summaries/summary_1760346825"`