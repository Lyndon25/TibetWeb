"""Git operations stub for testing."""
import os


def is_git_repo(path: str) -> bool:
    return os.path.isdir(os.path.join(path, '.git'))


def git_add(repo_path: str, *args) -> tuple[bool, str]:
    import subprocess
    try:
        r = subprocess.run(['git', 'add'] + list(args), cwd=repo_path,
                           capture_output=True, text=True, timeout=30)
        return r.returncode == 0, r.stderr
    except Exception as e:
        return False, str(e)


def git_commit(repo_path: str, *args) -> tuple[bool, str]:
    import subprocess
    try:
        r = subprocess.run(['git', 'commit', '-m'] + list(args), cwd=repo_path,
                           capture_output=True, text=True, timeout=30)
        return r.returncode == 0, r.stderr
    except Exception as e:
        return False, str(e)


def git_push(repo_path: str, *args) -> tuple[bool, str]:
    import subprocess
    try:
        cmd = ['git', 'push']
        if args:
            cmd.extend(args)
        r = subprocess.run(cmd, cwd=repo_path,
                           capture_output=True, text=True, timeout=60)
        return r.returncode == 0, r.stderr
    except Exception as e:
        return False, str(e)
