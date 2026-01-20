from pathlib import Path

from pyjobshop import Model, ProblemData


def parse_instance(loc: Path) -> Model:
    """
    Parses a problem instance from a file and returns a ProblemData instance.
    Parameters
    ----------
    loc
        The location of the problem instance file.
    test
        Whether the build model is also solved to test.
    add_setup_times
        Whether setup times (contamination and spread between fermentation constraints) should be added to the model.
    add_no_wait
        Whether the no waits should be added to the model.
    Returns
    -------
    ProblemData
        The problem data instance.
    """

    if not loc.exists():
        raise FileNotFoundError(f"Instance file not found: {loc}")

    with loc.open("r", encoding="utf-8") as f:
        json_str = f.read()

    problem_data = ProblemData.from_json(json_str)
    model = Model.from_data(problem_data)

    return model
