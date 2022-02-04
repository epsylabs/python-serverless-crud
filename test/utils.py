import json
import pathlib


def load_event(path):
    event_path = pathlib.Path(__file__).parent.parent.resolve().joinpath(f"events/{path}")
    with open(event_path) as f:
        return json.load(f)
