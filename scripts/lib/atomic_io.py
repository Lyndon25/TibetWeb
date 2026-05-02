"""Atomic file I/O with backup and rollback support."""
import os
import shutil
import tempfile


def atomic_write(path: str, content: str, encoding: str = 'utf-8') -> None:
    """
    Write content to path atomically with automatic backup.
    On failure, the original file is restored.
    """
    path = os.path.abspath(path)
    backup = path + '.backup'
    tmp = None

    # Create backup if file exists
    if os.path.exists(path):
        shutil.copy2(path, backup)

    try:
        fd, tmp = tempfile.mkstemp(
            dir=os.path.dirname(path) or '.',
            suffix='.tmp'
        )
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            f.write(content)
        shutil.move(tmp, path)
    except Exception:
        # Rollback on failure
        if os.path.exists(backup):
            shutil.move(backup, path)
        raise
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
        # Clean up backup on success
        if os.path.exists(backup) and os.path.exists(path):
            try:
                os.remove(backup)
            except OSError:
                pass


def read_file(path: str, encoding: str = 'utf-8') -> str:
    """Read file content safely."""
    with open(path, 'r', encoding=encoding) as f:
        return f.read()
