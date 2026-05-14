"""Git operations for the tibet-publish pipeline."""
import os
import subprocess

GIT_USER_NAME = "Lyndon25"
GIT_USER_EMAIL = "lyndon25@tibetride.com"


def is_git_repo(path: str) -> bool:
    return os.path.isdir(os.path.join(path, '.git'))


def ensure_git_config(repo_path: str):
    """Set git user.name/user.email if not already configured."""
    for key, value in [('user.name', GIT_USER_NAME), ('user.email', GIT_USER_EMAIL)]:
        try:
            r = subprocess.run(['git', '-C', repo_path, 'config', key],
                               capture_output=True, text=True)
            if not r.stdout.strip():
                subprocess.run(['git', '-C', repo_path, 'config', key, value],
                              capture_output=True)
        except Exception:
            pass


def git_add(repo_path: str, *args) -> tuple[bool, str]:
    try:
        r = subprocess.run(['git', 'add'] + list(args), cwd=repo_path,
                           capture_output=True, text=True, timeout=30)
        return r.returncode == 0, r.stderr
    except Exception as e:
        return False, str(e)


def git_commit(repo_path: str, *args) -> tuple[bool, str]:
    ensure_git_config(repo_path)
    try:
        r = subprocess.run(['git', 'commit', '-m'] + list(args), cwd=repo_path,
                           capture_output=True, text=True, timeout=30)
        return r.returncode == 0, r.stderr
    except Exception as e:
        return False, str(e)


def git_push(repo_path: str, *args) -> tuple[bool, str]:
    try:
        cmd = ['git', 'push']
        if args:
            cmd.extend(args)
        r = subprocess.run(cmd, cwd=repo_path,
                           capture_output=True, text=True, timeout=60)
        return r.returncode == 0, r.stderr
    except Exception as e:
        return False, str(e)
