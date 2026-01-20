#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
import uuid
from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np
import pandas as pd
from tabulate import tabulate  # type: ignore[import-untyped]

from src.parse import parse_instance
from src.warmstart import find_initial_solution_by_solving_per_job

# --------- Defaults (match your current script) ----------
DEFAULT_OUTPUT_DIR = "experiments/results"
MEMORY_LIMIT_IN_GB = 0.5


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Solve scheduling instances with optional warmstart and write results.")

    p.add_argument(
        "--instance-name",
        type=str,
        required=True,
        help="Name of the instance to solve.",
    )
    p.add_argument(
        "--instances-dir",
        type=Path,
        default=Path("instances"),
        help="Directory containing the instance .json files.",
    )
    p.add_argument(
        "--time-limit",
        type=float,
        default=60,
        help="Solver time limit in seconds.",
    )
    msg = "Number of worker threads to use for solving a single instance." "Default is the number of available CPU cores."
    p.add_argument("--num-workers", type=int, help=msg)
    p.add_argument(
        "--warmstart",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable or disable warmstart initialization (default: disabled).",
    )

    p.add_argument(
        "--solver",
        default="cpoptimizer",
        help="Underlying solver name (default: cpoptimizer).",
    )

    p.add_argument(
        "--display",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Show solver progress output if supported.",
    )

    p.add_argument(
        "--print-result",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Print final result summary to stdout.",
    )

    p.add_argument(
        "--print-sol",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Print solution details to stdout.",
    )

    p.add_argument(
        "--summary-dir",
        type=Path,
        default=Path(""),
        help="Optional directory for storing the summaries. " "Default is summary_<date>.csv in the current working directory.",
    )

    return p


def safe_tabulate(df: pd.DataFrame) -> str:
    return tabulate(df, headers="keys", tablefmt="pretty", showindex=False)


def main(argv: Optional[Sequence[str]] = None) -> int:
    # set_memory_limit(MEMORY_LIMIT_IN_GB)

    parser = make_parser()
    args = parser.parse_args(argv)
    instance_name = args.instance_name

    warmstart = True if args.warmstart else False
    time_limit = args.time_limit
    solver = args.solver

    summary_csv_path: Path
    summary_csv_path = Path(
        f"{args.summary_dir}/summary_{instance_name[:-5]}_TL{time_limit}_S{solver}_W{warmstart}" f"_{uuid.uuid4().hex}.csv"
    )

    summary_list: list[dict[str, Any]] = []

    print(
        f"Running {instance_name} instance. "
        f"Warmstart: {warmstart}. "
        f"Time limit: {args.time_limit}s,"
        f"Memory limit: {MEMORY_LIMIT_IN_GB}GB,"
    )

    try:
        if instance_name.endswith(".json"):
            instance_path = args.instances_dir / instance_name
        else:
            instance_path = args.instances_dir / f"{instance_name}.json"
        if not instance_path.exists():
            print(f"[WARN] Instance file not found: {instance_path}")

        model = parse_instance(instance_path)

        # Warmstart
        start_warmstart = time.time()
        solution_per_job = None
        warmstart_makespan: Optional[float] = None

        if args.warmstart:
            print("Start warmstart")
            solution_per_job, warmstart_makespan = find_initial_solution_by_solving_per_job(
                data=model.data(),
                solver=args.solver,
                time_limit=float("inf"),
            )
        end_warmstart = time.time()

        # Store the warmstarted initial solution
        initial_solution = solution_per_job if args.warmstart else None

        # Solve
        print(
            f"Starting solve: instance={instance_name}, "
            f"solver={args.solver}, "
            f"time_limit={args.time_limit},"
            f"warmstart={'yes' if args.warmstart else 'no'}"
        )

        result = model.solve(
            solver=args.solver, time_limit=args.time_limit, num_workers=args.num_workers, initial_solution=initial_solution
        )

        # Collect result
        result_dict: dict[str, Any] = {
            "status": result.status,
            "objective": result.objective,
            "runtime": result.runtime,
            "warmstart_time": np.round(end_warmstart - start_warmstart, 2) if args.warmstart else 0.0,
            "lower_bound": result.lower_bound,
            "gap": np.round(100 * (result.objective - result.lower_bound) / result.lower_bound, 3),
        }
        config: dict[str, Any] = {
            "time_limit": float(args.time_limit),
            "solver": args.solver,
            "instance_name": instance_name,
            "warmstart": args.warmstart,
            "warmstart_makespan": warmstart_makespan,
        }

        summary = result_dict | config
        summary_list.append(summary)
        summary_df = pd.DataFrame(summary_list)
        summary_df.to_csv(summary_csv_path, index=False)

        print(safe_tabulate(summary_df))

    except TimeoutError:
        config = {
            "time_limit": float(args.time_limit),
            "solver": args.solver,
            "instance_name": instance_name,
            "warmstart": warmstart,
            "warmstart_makespan": None,
        }
        result_dict = {
            "status": "Time-Limit-Exception",
            "objective": None,
            "runtime": None,
            "warmstart_time": None,
            "lower_bound": None,
            "gap": None,
        }
        summary = result_dict | config
        summary_list.append(summary)
        summary_df = pd.DataFrame(summary_list)
        summary_df.to_csv(summary_csv_path, index=False)
        print("[TIMEOUT] summary written.")
        print(safe_tabulate(summary_df))

    except MemoryError as e:
        # Continue with next instance instead of crashing the whole batch
        config = {
            "time_limit": float(args.time_limit),
            "solver": args.solver,
            "instance_name": instance_name,
            "warmstart": warmstart,
            "warmstart_makespan": None,
        }
        # Collect result
        result_dict = {
            "status": "Memory-Exception",
            "objective": None,
            "runtime": None,
            "warmstart_time": None,
            "lower_bound": None,
            "gap": None,
        }

        summary = result_dict | config
        summary_list.append(summary)
        summary_df = pd.DataFrame(summary_list)
        summary_df.to_csv(summary_csv_path, index=False)

        print(f"[ERROR] Instance '{instance_name}' failed with: {e!r}")

    except Exception as e:
        # Continue with next instance instead of crashing the whole batch
        config = {
            "time_limit": float(args.time_limit),
            "solver": args.solver,
            "instance_name": instance_name,
            "warmstart": warmstart,
            "warmstart_makespan": None,
        }
        # Collect result
        result_dict = {
            "status": f"{e!r}",
            "objective": None,
            "runtime": None,
            "warmstart_time": None,
            "lower_bound": None,
            "gap": None,
        }

        summary = result_dict | config
        summary_list.append(summary)
        summary_df = pd.DataFrame(summary_list)
        summary_df.to_csv(summary_csv_path, index=False)

        print(f"[ERROR] Instance '{instance_name}' failed with: {e!r}")

    print(f"Done. Summary written to: {summary_csv_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
