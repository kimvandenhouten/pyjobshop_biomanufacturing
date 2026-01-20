from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from pyjobshop.plot.utils import get_colors as _get_colors
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution


def plot_machine_gantt_one_job(
    solution: Solution,
    data: ProblemData,
    resources: list[int] | None = None,
    plot_labels: bool = False,
    ax: Axes | None = None,
    job: int | None = None,
):
    """
    Plots a Gantt chart of the solution, where each row represents a machine
    and each bar represents a task processed on that machine.

    Parameters
    ----------
    solution
        A solution to the problem.
    data
        The problem data instance.
    resources
        The resources (by index) to plot and in which order they should appear
        (from top to bottom). Defaults to all resources in the data instance.
    plot_labels
        Whether to plot the task names as labels.
    ax
        Axes object to draw the plot on. One will be created if not provided.
    """
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(12, 8))
        assert ax is not None  # for linting

    if resources is None:
        resources = list(range(data.num_resources))

    # Tasks belonging to the same job get the same color. Task that do not
    # belong to a job are colored grey.
    task2color = defaultdict(lambda: "grey")
    colors = _get_colors()
    for idx, task in enumerate(data.tasks):
        if task.job is not None:
            task2color[idx] = colors[task.job % len(colors)]

    for idx, task_data in enumerate(solution.tasks):
        if data.tasks[idx].job == job or job is None:
            kwargs = {
                "color": task2color[idx],
                "linewidth": 1,
                "edgecolor": "black",
                "alpha": 0.75,
            }
            duration = task_data.end - task_data.start
            if duration > 0:
                for resource in task_data.resources:
                    if resource not in resources:
                        continue  # skip resources not in the order

                    ax.barh(
                        resources.index(resource),
                        duration,
                        left=task_data.start,
                        **kwargs,
                    )

                    if plot_labels:
                        label = f"{data.tasks[idx].name}" or f"{idx}"
                        # label = f"{data.tasks[idx].job}"
                        ax.text(
                            task_data.start + duration / 2,
                            resources.index(resource),
                            label,
                            ha="center",
                            va="center",
                        )

        labels = [data.resources[idx].name or f"Machine {idx}" for idx in resources]

        ax.set_yticks(ticks=range(len(labels)), labels=labels)
        # ax.set_ylim(ax.get_ylim()[::-1])

        # ax.set_xlim(0, ax.get_xlim()[1])  # start time at zero
        ax.set_xlabel("Time")
        ax.set_title("Solution")


def plot_machine_gantt(
    solution: Solution,
    data: ProblemData,
    resources: list[int] | None = None,
    plot_labels: bool = False,
    ax: Axes | None = None,
):
    """
    Plots a Gantt chart of the solution, where each row represents a machine
    and each bar represents a task processed on that machine.

    Parameters
    ----------
    solution
        A solution to the problem.
    data
        The problem data instance.
    resources
        The resources (by index) to plot and in which order they should appear
        (from top to bottom). Defaults to all resources in the data instance.
    plot_labels
        Whether to plot the task names as labels.
    ax
        Axes object to draw the plot on. One will be created if not provided.
    """
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(20, 8))
        assert ax is not None  # for linting

    if resources is None:
        resources = list(range(data.num_resources))

    # Tasks belonging to the same job get the same color. Task that do not
    # belong to a job are colored grey.
    task2color = defaultdict(lambda: "grey")
    colors = _get_colors()
    for idx, task in enumerate(data.tasks):
        if task.job is not None:
            task2color[idx] = colors[task.job % len(colors)]

    if len(data.jobs) > 1:
        label_mode = "job"
    else:
        label_mode = "task"

    print(f"The label mode is {label_mode}")
    for idx, task_data in enumerate(solution.tasks):
        kwargs = {
            "color": task2color[idx],
            "linewidth": 1,
            "edgecolor": "black",
            "alpha": 0.75,
        }
        duration = task_data.end - task_data.start
        if duration > 0:
            for resource in task_data.resources:
                if resource not in resources:
                    continue  # skip resources not in the order

                ax.barh(
                    resources.index(resource),
                    duration,
                    left=task_data.start,
                    **kwargs,
                )

                if plot_labels:
                    if label_mode == "job":
                        label = f"{data.jobs[data.tasks[idx].job].name}" or f"{idx}"
                    else:
                        label = f"{data.tasks[idx].name}"
                    if duration > 5:
                        ax.text(
                            task_data.start + duration / 2,
                            resources.index(resource),
                            label,
                            ha="center",
                            va="center",
                        )

    labels = [data.resources[idx].name or f"Machine {idx}" for idx in resources]

    ax.set_yticks(ticks=range(len(labels)), labels=labels)
    ax.set_ylim(ax.get_ylim()[::-1])

    ax.set_xlim(0, ax.get_xlim()[1])  # start time at zero
    ax.set_xlabel("Time")
    ax.set_title("Solution")
