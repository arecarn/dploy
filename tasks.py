"""
Project Tasks that can be invoked using using the program "invoke" or "inv"
"""

import os

from invoke import task

# disable the check for unused-arguments to ignore unused ctx parameter in tasks
# pylint: disable=unused-argument

IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    # setting 'shell' is a work around for issue #345 of invoke
    RUN_ARGS = {"pty": False, "shell": r"C:\Windows\System32\cmd.exe"}
else:
    RUN_ARGS = {"pty": True}


def get_files():
    """
    Get the files to run analysis on
    """
    files = [
        "dploy",
        "tests",
        "tasks.py",
    ]
    files_string = " ".join(files)
    return files_string


@task
def setup(ctx) -> None:
    """
    Install python requirements
    """
    ctx.run("uv sync", **RUN_ARGS)


@task
def clean(ctx) -> None:
    """
    Clean repository using git
    """
    ctx.run("git clean --interactive", **RUN_ARGS)


@task
def lint(ctx):
    """
    Run pylint, ruff, and ty on this module
    """
    cmds = ["pylint --output-format=parseable", "ruff check", "ty check"]
    base_cmd = "uv run {cmd} {files}"


    for cmd in cmds:
        ctx.run(base_cmd.format(cmd=cmd, files=get_files()), **RUN_ARGS)


@task
def reformat_check(ctx) -> None:
    """
    Run formatting check
    """
    cmd = "ruff format --check"
    base_cmd = "uv run {cmd} {files}"
    ctx.run(base_cmd.format(cmd=cmd, files=get_files()), **RUN_ARGS)


@task
def reformat(ctx) -> None:
    """
    Run formatting
    """
    cmd = "ruff format"
    base_cmd = "uv run {cmd} {files}"
    ctx.run(base_cmd.format(cmd=cmd, files=get_files()), **RUN_ARGS)


@task
def metrics(ctx) -> None:
    """
    Run radon code metrics on this module
    """
    cmd = "uv run radon {metric} --min B {files}"
    metrics_to_run = ["cc", "mi"]
    for metric in metrics_to_run:
        ctx.run(cmd.format(metric=metric, files=get_files()), **RUN_ARGS)


@task()
def test(ctx) -> None:
    """
    Test Task
    """
    cmd = "uv run pytest --cov-report term-missing --cov=dploy --color=no"
    ctx.run(cmd, **RUN_ARGS)


# pylint: disable=redefined-builtin
@task(test, lint, reformat_check, metrics)
def all(ctx) -> None:
    """
    Run all CI tasks: test, lint, reformat_check, and metrics
    """


@task(clean)
def build(ctx) -> None:
    """
    Task to build an executable using pyinstaller
    """
    cmd = "uv run pyinstaller -n dploy --onefile " + os.path.join(
        "dploy", "__main__.py"
    )
    ctx.run(cmd, **RUN_ARGS)
