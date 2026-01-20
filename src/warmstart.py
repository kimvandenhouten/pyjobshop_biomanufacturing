from copy import copy, deepcopy

from pyjobshop import Job, Mode, Model, ProblemData, Solution, Task, TaskData


def filter_problem_data_per_job(data: ProblemData, old_job_index: int) -> tuple[ProblemData, dict, dict]:
    """
    Filters the problem data to create a subproblem for a specific job.

    Args:
        data (ProblemData): The complete problem data containing jobs, tasks, resources, modes, and constraints.
        old_job_index (int): The index of the job to filter from the problem data.

    Returns:
        tuple: A tuple containing:
            - ProblemData: The filtered problem data for the specified job.
            - dict: A mapping of new task indices to old task indices.
            - dict: A mapping of new mode indices to old mode indices.
    """
    old_job = deepcopy(data.jobs[old_job_index])
    tasks = []
    modes_translation = {}
    modes_translation_reversed = {}
    task_translation = {}
    task_translation_reversed = {}

    new_task_index = 0
    new_mode_index = 0

    modes_for_problem_data = []
    for old_task_index in old_job.tasks:
        # keep track of a translation dict in both directions
        task_translation[new_task_index] = old_task_index
        task_translation_reversed[old_task_index] = new_task_index
        task = data.tasks[old_task_index]
        tasks.append(task)

        modes = []
        for old_mode_index, mode in enumerate(data.modes):
            if mode.task == old_task_index:
                modes.append(mode)
                modes_translation[new_mode_index] = old_mode_index
                modes_translation_reversed[old_mode_index] = new_mode_index
                new_mode_index += 1
                mode_translated = Mode(task=new_task_index, resources=mode.resources, duration=mode.duration, demands=mode.demands)
                modes_for_problem_data.append(mode_translated)

        new_task_index += 1

    new_job_data = Job(tasks=[task_translation_reversed[t] for t in old_job.tasks])
    new_task_data = [Task(job=0, allow_idle=task.allow_idle) for task in tasks]

    constraints = deepcopy(data.constraints)

    # List of constraints that we care about while solving the subproblem
    allowed_constraints = [
        "start_before_end",
        "start_before_start",
        "end_before_start",
        "end_before_end",
        "consecutive",
        "identical_resources",
        "different_resources",
        "same_sequence",
        "setup_times",
    ]

    # Try to create a fresh instance of the same class; if that fails, use a simple namespace.
    new_constraints = type(constraints)()  # assumes no-arg constructor

    tasks_set = set(old_job.tasks)

    for cname in allowed_constraints:
        if not hasattr(constraints, cname):
            continue

        cons_list = getattr(constraints, cname) or []
        valid_cons = []

        for cons in cons_list:
            # Must have task1 and task2 attributes
            if not (hasattr(cons, "task1") and hasattr(cons, "task2")):
                print(f"Warning but cons of type {cname} does not have a " f"task 1 and task 2 attribute")
                continue

            t1, t2 = cons.task1, cons.task2

            # Keep only if both tasks exist in job_data.tasks (per your spec)
            if t1 in tasks_set and t2 in tasks_set:
                # copy the constraint object so we don't mutate the original
                cons_copy = copy(cons)

                # overwrite tasks with the translated names
                cons_copy.task1 = task_translation_reversed[t1]
                cons_copy.task2 = task_translation_reversed[t2]

                valid_cons.append(cons_copy)

        setattr(new_constraints, cname, valid_cons)

    cname = "mode_dependencies"
    cons_list = getattr(constraints, cname) or []
    valid_cons = []
    for cons in cons_list:
        # Must have task1 and task2 attributes
        if not (hasattr(cons, "mode1") and hasattr(cons, "modes2")):
            print(f"Warning but cons of type {cname} does not have a " f"mode 1 and mode 2 attribute")
            continue

        mode1_old_index, modes2_old_indices = cons.mode1, cons.modes2
        old_mode1 = data.modes[mode1_old_index]
        if old_mode1.task in tasks_set:
            # copy the constraint object so we don't mutate the original
            cons_copy = copy(cons)

            # overwrite tasks with the translated names
            cons_copy.mode1 = modes_translation_reversed[mode1_old_index]
            cons_copy.modes2 = [modes_translation_reversed[mode2] for mode2 in modes2_old_indices]

            valid_cons.append(cons_copy)
    setattr(new_constraints, cname, valid_cons)

    new_data = ProblemData(
        jobs=[new_job_data], tasks=new_task_data, resources=data.resources, modes=modes_for_problem_data, constraints=new_constraints
    )

    return new_data, task_translation, modes_translation


def find_initial_solution_by_solving_per_job(data: ProblemData, time_limit: float = float("inf"), solver: str = "cpoptimizer") -> Solution:
    """
    Finds an initial solution for the problem by solving each job independently.

    Args:
        data (ProblemData): The problem data containing jobs, tasks, resources, modes, and constraints.
        time_limit (float, optional): The time limit for solving each job's subproblem. Defaults to None.

    Returns:
        Solution: The initial solution constructed by combining the solutions of individual jobs.
    """
    relative_time_point = 0
    scheduled_tasks: list[TaskData] = []
    for job_index in range(0, len(data.jobs)):
        print(f"Start solving job {job_index}")
        # Create a new ProblemData object that filters based on job_index
        new_data, task_translation, modes_translation = filter_problem_data_per_job(data, job_index)

        # Create a new model from this problem data and solve
        new_model = Model().from_data(new_data)
        print(new_model.summary())
        result = new_model.solve(solver=solver, display=False, time_limit=time_limit)

        # The solution of this model is a partial solution to the full problem instance
        partial_solution = result.best

        # We store the makespan to postpone all later jobs by this makespan
        makespan = result.best.makespan
        print(f"makespan {makespan}")

        # Store the scheduling information of each task
        for old_task_data in partial_solution.tasks:
            new_task_data = TaskData(
                mode=modes_translation[old_task_data.mode],
                start=old_task_data.start + relative_time_point,
                end=old_task_data.end + relative_time_point,
                resources=old_task_data.resources,
            )
            scheduled_tasks.append(new_task_data)

        relative_time_point += makespan + 12  # This buffer is needed for the spread between the fermentation
        print(relative_time_point)

    # The initial solution for the warmstart combines all the jobs that are solved independently
    initial_solution = Solution(data, scheduled_tasks)
    assert len(initial_solution.tasks) == len(data.tasks)

    return initial_solution, relative_time_point


if __name__ == "__main__":
    # Create a simple model from the PyJobShop documentation
    model = Model()
    jobs = [model.add_job() for _ in range(4)]
    nr_jobs = len(jobs)
    tasks = [[model.add_task(job=job) for _ in range(2)] for job in jobs]
    nr_tasks = sum([len(job_tasks) for job_tasks in tasks])
    machines = [model.add_machine() for _ in range(2)]
    nr_machines = len(machines)

    for job in range(len(jobs)):
        for task in tasks[job]:
            for machine in machines:
                duration = job + 1
                model.add_mode(task, machine, duration)

    for job in range(len(jobs)):
        tasks_job = tasks[job]
        for t in range(len(tasks_job) - 1):
            model.add_end_before_start(tasks_job[t], tasks_job[t + 1])
            model.add_identical_resources(tasks_job[t], tasks_job[t + 1])
    print("The original model has:")
    print(model.summary())
    print("\n")

    # Solve the model without warmstart
    SOLVER = "cpoptimizer"
    model.solve(solver=SOLVER, display=False)

    # Solve the mode with warmstart
    initial_solution, relative_time_point = find_initial_solution_by_solving_per_job(data=model.data())
    model.solve(initial_solution=initial_solution, display=True, solver=SOLVER)
