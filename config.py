import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".toolbox"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


REPOS_FILE = CONFIG_DIR / "repos.json"


def load_repos():
    if REPOS_FILE.exists():
        return json.loads(REPOS_FILE.read_text())
    return {}


def save_repos(repos):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    REPOS_FILE.write_text(json.dumps(repos, indent=2))


def get_github_token():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    config = load_config()
    token = config.get("github_token")
    if not token:
        token = input("GitHub PAT: ").strip()
        config["github_token"] = token
        save_config(config)
    return token
