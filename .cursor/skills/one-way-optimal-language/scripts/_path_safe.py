"""Validate file paths for living-reference CLI scripts (stdlib only)."""
import os

# Largest reference Markdown file the scripts will read (refresh or export).
MAX_INPUT_BYTES = 10 * 1024 * 1024

# Largest export artifact written beside an existing file.
MAX_OUTPUT_BYTES = 50 * 1024 * 1024


class PathValidationError(ValueError):
    """The path is not safe or not usable."""


def _reject_traversal(path):
    """Reject obvious path traversal in the argument before touching the filesystem."""
    if not path or not isinstance(path, str):
        raise PathValidationError('path must be a non-empty string')
    if '\x00' in path:
        raise PathValidationError('path contains a null byte')
    if os.path.isabs(path) and '..' in path.split(os.sep):
        raise PathValidationError('path must not contain .. segments')
    parts = path.replace('\\', '/').split('/')
    if '..' in parts:
        raise PathValidationError('path must not contain ..')


def validate_user_path(path, must_exist=True):
    """Resolve a user-supplied reference or output path to a regular file path.

    Uses realpath resolution. Symlinks are followed; the result must be a normal file.
    """
    _reject_traversal(path)
    try:
        resolved = os.path.realpath(path)
    except OSError as error:
        raise PathValidationError('cannot resolve path: %s' % error) from error
    _reject_traversal(resolved)
    if must_exist:
        if not os.path.isfile(resolved):
            if os.path.isdir(resolved):
                raise PathValidationError('path is a directory, not a file: %s' % path)
            raise PathValidationError('file does not exist: %s' % path)
    else:
        parent = os.path.dirname(resolved)
        if not os.path.isdir(parent):
            raise PathValidationError('output directory does not exist: %s' % parent)
    return resolved


def assert_input_size(path):
    """Ensure the file is within MAX_INPUT_BYTES."""
    try:
        size = os.path.getsize(path)
    except OSError as error:
        raise PathValidationError('cannot stat file: %s' % error) from error
    if size > MAX_INPUT_BYTES:
        raise PathValidationError(
            'file exceeds %d MiB limit (%d bytes)' % (MAX_INPUT_BYTES // (1024 * 1024), size))


def assert_output_parent_writable(path):
    """Output path must not replace a directory; parent must exist."""
    resolved = validate_user_path(path, must_exist=False)
    if os.path.exists(resolved) and os.path.isdir(resolved):
        raise PathValidationError('output path is a directory: %s' % path)
    return resolved
