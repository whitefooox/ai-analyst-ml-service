from dataclasses import dataclass
from environs import Env


@dataclass
class Config:
    debug: bool


def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(debug=env.bool("DEBUG", default=False))
