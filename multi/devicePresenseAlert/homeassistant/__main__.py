"""Starts home assistant."""
from __future__ import print_function

import argparse
import os
import platform
import subprocess
import sys
import threading

from typing import Optional, List

from homeassistant.const import (
    __version__,
    EVENT_HOMEASSISTANT_START,
    REQUIRED_PYTHON_VER,
    REQUIRED_PYTHON_VER_WIN,
    RESTART_EXIT_CODE,
)
from homeassistant.util.async import run_callback_threadsafe


def monkey_patch_asyncio():
    """Replace weakref.WeakSet to address Python 3 bug.

    Under heavy threading operations that schedule calls into
    the asyncio event loop, Task objects are created. Due to
    a bug in Python, GC may have an issue when switching between
    the threads and objects with __del__ (which various components
    in HASS have).

    This monkey-patch removes the weakref.Weakset, and replaces it
    with an object that ignores the only call utilizing it (the
    Task.__init__ which calls _all_tasks.add(self)). It also removes
    the __del__ which could trigger the future objects __del__ at
    unpredictable times.

    The side-effect of this manipulation of the Task is that
    Task.all_tasks() is no longer accurate, and there will be no
    warning emitted if a Task is GC'd while in use.

    On Python 3.6, after the bug is fixed, this monkey-patch can be
    disabled.

    See https://bugs.python.org/issue26617 for details of the Python
    bug.
    """
    # pylint: disable=no-self-use, protected-access, bare-except
    import asyncio.tasks

    class IgnoreCalls:
        """Ignore add calls."""

        def add(self, other):
            """No-op add."""
            return

    asyncio.tasks.Task._all_tasks = IgnoreCalls()
    try:
        del asyncio.tasks.Task.__del__
    except:
        pass


def validate_python() -> None:
    """Validate we're running the right Python version."""
    if sys.platform == "win32" and \
       sys.version_info[:3] < REQUIRED_PYTHON_VER_WIN:
        print("Home Assistant requires at least Python {}.{}.{}".format(
            *REQUIRED_PYTHON_VER_WIN))
        sys.exit(1)
    elif sys.version_info[:3] < REQUIRED_PYTHON_VER:
        print("Home Assistant requires at least Python {}.{}.{}".format(
            *REQUIRED_PYTHON_VER))
        sys.exit(1)


def ensure_config_path(config_dir: str) -> None:
    """Validate the configuration directory."""
    import homeassistant.config as config_util
    lib_dir = os.path.join(config_dir, 'deps')

    # Test if configuration directory exists
    if not os.path.isdir(config_dir):
        if config_dir != config_util.get_default_config_dir():
            print(('Fatal Error: Specified configuration directory does '
                   'not exist {} ').format(config_dir))
            sys.exit(1)

        try:
            os.mkdir(config_dir)
        except OSError:
            print(('Fatal Error: Unable to create default configuration '
                   'directory {} ').format(config_dir))
            sys.exit(1)

    # Test if library directory exists
    if not os.path.isdir(lib_dir):
        try:
            os.mkdir(lib_dir)
        except OSError:
            print(('Fatal Error: Unable to create library '
                   'directory {} ').format(lib_dir))
            sys.exit(1)


def ensure_config_file(config_dir: str) -> str:
    """Ensure configuration file exists."""
    import homeassistant.config as config_util
    config_path = config_util.ensure_config_exists(config_dir)

    if config_path is None:
        print('Error getting configuration path')
        sys.exit(1)

    return config_path


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    import homeassistant.config as config_util
    parser = argparse.ArgumentParser(
        description="Home Assistant: Observe, Control, Automate.")
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument(
        '-c', '--config',
        metavar='path_to_config_dir',
        default=config_util.get_default_config_dir(),
        help="Directory that contains the Home Assistant configuration")
    parser.add_argument(
        '--demo-mode',
        action='store_true',
        help='Start Home Assistant in demo mode')
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Start Home Assistant in debug mode')
    parser.add_argument(
        '--open-ui',
        action='store_true',
        help='Open the webinterface in a browser')
    parser.add_argument(
        '--skip-pip',
        action='store_true',
        help='Skips pip install of required packages on startup')
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose logging to file.")
    parser.add_argument(
        '--pid-file',
        metavar='path_to_pid_file',
        default=None,
        help='Path to PID file useful for running as daemon')
    parser.add_argument(
        '--log-rotate-days',
        type=int,
        default=None,
        help='Enables daily log rotation and keeps up to the specified days')
    parser.add_argument(
        '--runner',
        action='store_true',
        help='On restart exit with code {}'.format(RESTART_EXIT_CODE))
    parser.add_argument(
        '--script',
        nargs=argparse.REMAINDER,
        help='Run one of the embedded scripts')
    if os.name == "posix":
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run Home Assistant as daemon')

    arguments = parser.parse_args()
    if os.name != "posix" or arguments.debug or arguments.runner:
        setattr(arguments, 'daemon', False)

    return arguments


def daemonize() -> None:
    """Move current process to daemon process."""
    # Create first fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # Decouple fork
    os.setsid()

    # Create second fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # redirect standard file descriptors to devnull
    infd = open(os.devnull, 'r')
    outfd = open(os.devnull, 'a+')
    sys.stdout.flush()
    sys.stderr.flush()
    os.dup2(infd.fileno(), sys.stdin.fileno())
    os.dup2(outfd.fileno(), sys.stdout.fileno())
    os.dup2(outfd.fileno(), sys.stderr.fileno())


def check_pid(pid_file: str) -> None:
    """Check that HA is not already running."""
    # Check pid file
    try:
        pid = int(open(pid_file, 'r').readline())
    except IOError:
        # PID File does not exist
        return

    # If we just restarted, we just found our own pidfile.
    if pid == os.getpid():
        return

    try:
        os.kill(pid, 0)
    except OSError:
        # PID does not exist
        return
    print('Fatal Error: HomeAssistant is already running.')
    sys.exit(1)


def write_pid(pid_file: str) -> None:
    """Create a PID File."""
    pid = os.getpid()
    try:
        open(pid_file, 'w').write(str(pid))
    except IOError:
        print('Fatal Error: Unable to write pid file {}'.format(pid_file))
        sys.exit(1)


def closefds_osx(min_fd: int, max_fd: int) -> None:
    """Make sure file descriptors get closed when we restart.

    We cannot call close on guarded fds, and we cannot easily test which fds
    are guarded. But we can set the close-on-exec flag on everything we want to
    get rid of.
    """
    from fcntl import fcntl, F_GETFD, F_SETFD, FD_CLOEXEC

    for _fd in range(min_fd, max_fd):
        try:
            val = fcntl(_fd, F_GETFD)
            if not val & FD_CLOEXEC:
                fcntl(_fd, F_SETFD, val | FD_CLOEXEC)
        except IOError:
            pass


def cmdline() -> List[str]:
    """Collect path and arguments to re-execute the current hass instance."""
    if sys.argv[0].endswith('/__main__.py'):
        modulepath = os.path.dirname(sys.argv[0])
        os.environ['PYTHONPATH'] = os.path.dirname(modulepath)
    return [sys.executable] + [arg for arg in sys.argv if arg != '--daemon']


def setup_and_run_hass(config_dir: str,
                       args: argparse.Namespace) -> Optional[int]:
    """Setup HASS and run."""
    from homeassistant import bootstrap

    # Run a simple daemon runner process on Windows to handle restarts
    if os.name == 'nt' and '--runner' not in sys.argv:
        nt_args = cmdline() + ['--runner']
        while True:
            try:
                subprocess.check_call(nt_args)
                sys.exit(0)
            except subprocess.CalledProcessError as exc:
                if exc.returncode != RESTART_EXIT_CODE:
                    sys.exit(exc.returncode)

    if args.demo_mode:
        config = {
            'frontend': {},
            'demo': {}
        }
        hass = bootstrap.from_config_dict(
            config, config_dir=config_dir, verbose=args.verbose,
            skip_pip=args.skip_pip, log_rotate_days=args.log_rotate_days)
    else:
        config_file = ensure_config_file(config_dir)
        print('Config directory:', config_dir)
        hass = bootstrap.from_config_file(
            config_file, verbose=args.verbose, skip_pip=args.skip_pip,
            log_rotate_days=args.log_rotate_days)

    if hass is None:
        return None

    if args.open_ui:
        def open_browser(event):
            """Open the webinterface in a browser."""
            if hass.config.api is not None:
                import webbrowser
                webbrowser.open(hass.config.api.base_url)

        run_callback_threadsafe(
            hass.loop,
            hass.bus.async_listen_once,
            EVENT_HOMEASSISTANT_START, open_browser
        )

    hass.start()
    return hass.exit_code


def try_to_restart() -> None:
    """Attempt to clean up state and start a new homeassistant instance."""
    # Things should be mostly shut down already at this point, now just try
    # to clean up things that may have been left behind.
    sys.stderr.write('Home Assistant attempting to restart.\n')

    # Count remaining threads, ideally there should only be one non-daemonized
    # thread left (which is us). Nothing we really do with it, but it might be
    # useful when debugging shutdown/restart issues.
    try:
        nthreads = sum(thread.is_alive() and not thread.daemon
                       for thread in threading.enumerate())
        if nthreads > 1:
            sys.stderr.write(
                "Found {} non-daemonic threads.\n".format(nthreads))

    # Somehow we sometimes seem to trigger an assertion in the python threading
    # module. It seems we find threads that have no associated OS level thread
    # which are not marked as stopped at the python level.
    except AssertionError:
        sys.stderr.write("Failed to count non-daemonic threads.\n")

    # Try to not leave behind open filedescriptors with the emphasis on try.
    try:
        max_fd = os.sysconf("SC_OPEN_MAX")
    except ValueError:
        max_fd = 256

    if platform.system() == 'Darwin':
        closefds_osx(3, max_fd)
    else:
        os.closerange(3, max_fd)

    # Now launch into a new instance of Home-Assistant. If this fails we
    # fall through and exit with error 100 (RESTART_EXIT_CODE) in which case
    # systemd will restart us when RestartForceExitStatus=100 is set in the
    # systemd.service file.
    sys.stderr.write("Restarting Home-Assistant\n")
    args = cmdline()
    os.execv(args[0], args)


def main() -> int:
    """Start Home Assistant."""
    if sys.version_info[:3] < (3, 5, 3):
        monkey_patch_asyncio()

    validate_python()

    args = get_arguments()

    if args.script is not None:
        from homeassistant import scripts
        return scripts.run(args.script)

    config_dir = os.path.join(os.getcwd(), args.config)
    ensure_config_path(config_dir)

    # Daemon functions
    if args.pid_file:
        check_pid(args.pid_file)
    if args.daemon:
        daemonize()
    if args.pid_file:
        write_pid(args.pid_file)

    exit_code = setup_and_run_hass(config_dir, args)
    if exit_code == RESTART_EXIT_CODE and not args.runner:
        try_to_restart()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
