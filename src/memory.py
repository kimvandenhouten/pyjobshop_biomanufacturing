import resource


def set_memory_limit(memory_limit_in_gb: float):
    if memory_limit_in_gb < 0.001:
        raise ValueError("Limit cannot be below 0.001 (~1MB)")
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    n_bytes = int(memory_limit_in_gb * 1024 * 1024 * 1024)
    print(f"n_bytes: {n_bytes}, soft: {soft}, hard: {hard}")
    if n_bytes > hard:
        print(
            f"Cannot set memory limit to {memory_limit_in_gb} GB, "
            f"as it exceeds the hard limit of {hard / (1024 ** 3):.2f} GB."
            f"Set to hard limit instead."
        )
        n_bytes = hard

    resource.setrlimit(resource.RLIMIT_AS, (n_bytes, hard))
