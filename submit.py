#!/usr/bin/env python3
import argparse
import json
import time
from pathlib import Path
from subprocess import run

JOBSCRIPT = """#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --time={walltime}
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --partition=compute
#SBATCH --mem-per-cpu=3968MB
#SBATCH --account=Research-EEMCS-ST
#SBATCH --output=slurm/output_{job_name}_%j.out
#SBATCH --error=slurm/error_{job_name}_%j.err
#SBATCH --mail-type=FAIL

uv run python benchmark_instance.py \\
  --instances-dir {instance_dir} \\
  --instance-name {instance_name} \\
  --time-limit {time_limit} \\
  --solver {solver} \\
  --num-workers {num_workers} \\
  {warmstart_flag} \\
  --summary-dir {summary_dir} \\
"""


def seconds2string(seconds: int) -> str:
    mins, seconds = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{seconds:02d}"


def main():
    ap = argparse.ArgumentParser(description="Submit SLURM jobs for benchmark runs.")
    ap.add_argument("--config", required=True, help="Path to config.json")
    ap.add_argument("--dry-run", action="store_true", help="Print jobscripts instead of submitting")
    ap.add_argument("--solve-dir", action="store_true", help="Solve all the instances from " "the provided directory")
    args = ap.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    instances_dir = cfg["instances_dir"]
    instances_dir = Path(instances_dir)

    if args.solve_dir:
        # Use filenames as instance names. If your benchmark expects stems, swap to p.stem below.
        instance_names = sorted([p.name for p in instances_dir.iterdir() if p.is_file()])
        if not instance_names:
            raise ValueError(f"No files found in {args.instances_dir}")
    else:
        instance_names = cfg["instance_names"]

    time_limits = cfg["time_limits"]
    buffer_wall_time = cfg["buffer_wall_time"]
    solvers = cfg["solvers"]
    warmstarts = cfg["warmstarts"]
    num_workers = cfg["num_workers"]
    experiment_name = cfg["experiment_name"]

    # We wil create a directory to store the summary CSV files
    start_jobs_submission = time.time()
    summary_dir = Path(f"summaries/summary_{experiment_name}_{int(start_jobs_submission)}")
    summary_dir.mkdir(parents=True, exist_ok=True)
    print(f"Summary directory created at: {summary_dir}")
    print(f'To combine all results later, run: \nuv run summarize.py --dir "{summary_dir}"')

    # Store the config dict into this summary dir as json
    config_path = summary_dir / "config.json"
    with open(config_path, "w", encoding="utf-8") as config_file:
        json.dump(cfg, config_file, indent=4)
    print(f"Config file saved at: {config_path}")

    # Loop through the different configurations and submit seperate job for each configuration
    for name in instance_names:
        for tl in time_limits:
            for ws in warmstarts:
                for solver in solvers:
                    job_name = f"{name[:-5]}-ws{ws}-tl{tl}-s{solver}="
                    walltime = seconds2string(tl + buffer_wall_time)
                    warmstart_flag = "--warmstart" if ws else "--no-warmstart"

                    jobscript = JOBSCRIPT.format(
                        job_name=job_name,
                        walltime=walltime,
                        instance_dir=instances_dir,
                        instance_name=name,
                        time_limit=tl,
                        solver=solver,
                        warmstart_flag=warmstart_flag,
                        num_workers=num_workers,
                        summary_dir=f"summaries/summary_{experiment_name}_{int(start_jobs_submission)}",
                    )

                    if args.dry_run:
                        print(jobscript)
                    else:
                        run(["sbatch"], input=jobscript, text=True, check=True)


if __name__ == "__main__":
    main()
