import base64
from nacl.public import PublicKey, SealedBox
import requests

API = "https://api.github.com"


class GitHub:
    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        })
        self._user = None

    @property
    def user(self):
        if not self._user:
            self._user = self.session.get(f"{API}/user").json()["login"]
        return self._user

    def list_repos(self, include_private=True):
        repos = []
        page = 1
        while True:
            resp = self.session.get(f"{API}/user/repos", params={
                "per_page": 100,
                "page": page,
                "affiliation": "owner",
                "sort": "updated",
            })
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            repos.extend(batch)
            page += 1
        return repos

    def _get_repo_public_key(self, repo):
        resp = self.session.get(f"{API}/repos/{self.user}/{repo}/actions/secrets/public-key")
        resp.raise_for_status()
        return resp.json()

    def _encrypt_secret(self, public_key_b64, value):
        public_key = PublicKey(base64.b64decode(public_key_b64))
        sealed = SealedBox(public_key).encrypt(value.encode())
        return base64.b64encode(sealed).decode()

    def set_secret(self, repo, name, value):
        key_data = self._get_repo_public_key(repo)
        encrypted = self._encrypt_secret(key_data["key"], value)
        resp = self.session.put(
            f"{API}/repos/{self.user}/{repo}/actions/secrets/{name}",
            json={"encrypted_value": encrypted, "key_id": key_data["key_id"]},
        )
        resp.raise_for_status()

    def set_secrets(self, repo, secrets):
        key_data = self._get_repo_public_key(repo)
        for name, value in secrets.items():
            encrypted = self._encrypt_secret(key_data["key"], value)
            resp = self.session.put(
                f"{API}/repos/{self.user}/{repo}/actions/secrets/{name}",
                json={"encrypted_value": encrypted, "key_id": key_data["key_id"]},
            )
            resp.raise_for_status()
            print(f"  {name} ok")

    def create_repo(self, name, private=True):
        resp = self.session.post(f"{API}/user/repos", json={
            "name": name,
            "private": private,
            "auto_init": True,
        })
        resp.raise_for_status()
        return resp.json()
