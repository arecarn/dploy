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
def setup(ctx):
    """
    Install python requirements
    """
    ctx.run("poetry install", **RUN_ARGS)


@task
def clean(ctx):
    """
    Clean repository using git
    """
    ctx.run("git clean --interactive", **RUN_ARGS)


@task
def lint(ctx):
    """
    Run pylint on this module
    """
    cmds = ["pylint --output-format=parseable", "flake8"]
    base_cmd = "poetry run {cmd} {files}"

    for cmd in cmds:
        ctx.run(base_cmd.format(cmd=cmd, files=get_files()), **RUN_ARGS)


@task
def reformat_check(ctx):
    """
    Run formatting check
    """
    cmd = "black --check"
    base_cmd = "poetry run {cmd} {files}"
    ctx.run(base_cmd.format(cmd=cmd, files=get_files()), **RUN_ARGS)


@task
def reformat(ctx):
    """
    Run formatting
    """
    cmd = "black"
    base_cmd = "poetry run {cmd} {files}"
    ctx.run(base_cmd.format(cmd=cmd, files=get_files()), **RUN_ARGS)


@task
def metrics(ctx):
    """
    Run radon code metrics on this module
    """
    cmd = "poetry run radon {metric} --min B {files}"
    metrics_to_run = ["cc", "mi"]
    for metric in metrics_to_run:
        ctx.run(cmd.format(metric=metric, files=get_files()), **RUN_ARGS)


@task()
def test(ctx):
    """
    Test Task
    """
    cmd = "poetry run pytest --cov-report term-missing --cov=dploy --color=no"
    ctx.run(cmd, **RUN_ARGS)


# pylint: disable=redefined-builtin
@task(test, lint, reformat_check)
def all(default=True):
    """
    All tasks minus
    """


@task(clean)
def build(ctx):
    """
    Task to build an executable using pyinstaller
    """
    cmd = "pyinstaller -n dploy --onefile " + os.path.join("dploy", "__main__.py")
    ctx.run(cmd, **RUN_ARGS)
