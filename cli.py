import subprocess
import sys
from pathlib import Path
from config import get_github_token, load_repos, save_repos
from github import GitHub

CLONE_DIR = Path("C:/src")

PROD_SECRETS = {
    "PROD_HOST": "167.86.90.67",
    "PROD_USERNAME": "root",
    "PROD_SSH_KEY": (Path.home() / ".ssh" / "id_rsa").read_text,
}


def cmd_repos_list(gh, args):
    repos = gh.list_repos()
    if not repos:
        print("No repositories found.")
        return
    name_width = max(len(r["name"]) for r in repos)
    for r in repos:
        visibility = "private" if r["private"] else "public "
        print(f"  {r['name']:<{name_width}}  {visibility}  {r['html_url']}")


def cmd_secrets_set(gh, args):
    if not args:
        print("Usage: python cli.py secrets set <repo>")
        sys.exit(1)
    repo = args[0]
    secrets = {}
    for name, value in PROD_SECRETS.items():
        secrets[name] = value() if callable(value) else value
    print(f"Setting secrets on {repo}:")
    gh.set_secrets(repo, secrets)
    print("Done.")


def cmd_secrets_google(gh, args):
    if not args:
        print("Usage: python cli.py secrets google <repo>")
        sys.exit(1)
    repo = args[0]
    value = input("NEXT_PUBLIC_GOOGLE_CLIENT_ID: ").strip()
    if not value:
        print("Aborted.")
        sys.exit(1)
    print(f"Setting secret on {repo}:")
    gh.set_secret(repo, "NEXT_PUBLIC_GOOGLE_CLIENT_ID", value)
    print("  NEXT_PUBLIC_GOOGLE_CLIENT_ID ok")
    print("Done.")


def pick_repo(gh):
    repos = gh.list_repos()
    for i, r in enumerate(repos, 1):
        print(f"  {i:3}. {r['name']}")
    choice = input("\nEnter number: ").strip()
    return repos[int(choice) - 1]["name"]


def cmd_setup(gh, args):
    repo = args[0] if args else pick_repo(gh)
    repos = load_repos()
    existing = repos.get(repo, {})
    domain = input(f"Domain [{existing.get('domain', '')}]: ").strip()
    local_dir = input(f"Local dev folder [{existing.get('local_dir', '')}]: ").strip()
    repos[repo] = {
        "domain": domain or existing.get("domain", ""),
        "local_dir": local_dir or existing.get("local_dir", ""),
    }
    save_repos(repos)
    print(f"Saved {repo}.")


def cmd_list(gh, args):
    repos = load_repos()
    if not repos:
        print("No repos registered. Run: python cli.py setup")
        return
    name_width = max(len(n) for n in repos)
    for name, info in repos.items():
        domain = info.get("domain", "")
        local_dir = info.get("local_dir", "")
        print(f"  {name:<{name_width}}  domain={domain or '-':<20}  dir={local_dir or '-'}")


def cmd_create(gh, args):
    name = input("Repo name: ").strip()
    if not name:
        print("Aborted.")
        sys.exit(1)
    print(f"Creating private repo {name}...")
    gh.create_repo(name)
    print("Setting prod secrets...")
    secrets = {}
    for k, v in PROD_SECRETS.items():
        secrets[k] = v() if callable(v) else v
    gh.set_secrets(name, secrets)
    clone_url = f"https://github.com/{gh.user}/{name}.git"
    dest = CLONE_DIR / name
    print(f"Cloning into {dest}...")
    result = subprocess.run(["git", "clone", clone_url, str(dest)])
    if result.returncode != 0:
        print(f"Clone failed. Run manually: git clone {clone_url} {dest}")
    else:
        print("Done.")


COMMANDS = {
    "repos list": cmd_repos_list,
    "secrets set": cmd_secrets_set,
    "secrets google": cmd_secrets_google,
    "create": cmd_create,
    "setup": cmd_setup,
    "list": cmd_list,
}


def main():
    args = sys.argv[1:]
    # Try two-word command first, then one-word
    cmd_key = " ".join(args[:2]) if len(args) >= 2 else ""
    if cmd_key in COMMANDS:
        gh = GitHub(get_github_token())
        COMMANDS[cmd_key](gh, args[2:])
    elif args and args[0] in COMMANDS:
        cmd_key = args[0]
        gh = GitHub(get_github_token())
        COMMANDS[cmd_key](gh, args[1:])
    else:
        print("Usage: python cli.py <command>")
        print()
        print("Commands:")
        print("  repos list             List your GitHub repositories")
        print("  secrets set <repo>     Set prod secrets on a repo")
        print("  secrets google <repo>  Set NEXT_PUBLIC_GOOGLE_CLIENT_ID")
        print("  create                 Create private repo, set secrets, clone to C:\\src")
        print("  setup [repo]           Register repo details (domain, local dir)")
        print("  list                   List registered repos")
        sys.exit(1)


if __name__ == "__main__":
    main()
