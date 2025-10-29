import json
from typing import Any, Dict


def load_config(config_file_path: str) -> Dict[str, Any]:
    """
    Load the configuration for a dataset.

    Parameters
    ----------
    config_file_path : str
        The config file path.

    Returns
    -------
    Dict[str, Any]
        A Python dictionary containing the configuration.
    """

    assert config_file_path.lower().endswith(
        ".json"
    ), f"provided file is not JSON | {config_file_path}"

    with open(config_file_path, "r") as f:
        config: Dict[str, Any] = json.load(f)

    return config
