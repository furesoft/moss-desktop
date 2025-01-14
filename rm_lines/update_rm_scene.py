import atexit
import os
import shutil
import subprocess
import tempfile
import time
import venv
from typing import List, Tuple

import colorama
from colorama import Fore
from slashr import SlashR

colorama.init()

WORK_DIR = os.path.dirname(__file__)
CACHE_DIR = os.path.join(WORK_DIR, ".cached")
REPO_URL = "https://github.com/ricklupton/rmscene.git"
REPO_CLONE_DIR = os.path.join(CACHE_DIR, "rmscene")
MODIFICATIONS_DIR = tempfile.mkdtemp()
VENV_DIR = os.path.join(CACHE_DIR, ".venv")
EXTRA_PACKAGES = ("poetry",)
VENV_BIN_DIR = os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin")
PIP_EXECUTABLE = os.path.join(VENV_BIN_DIR, "pip" + (".exe" if os.name == "nt" else ""))
PYTHON_EXECUTABLE = os.path.join(VENV_BIN_DIR, "python" + (".exe" if os.name == "nt" else ""))
SOURCE_DIR = os.path.join(MODIFICATIONS_DIR, "src", "rmscene")
TAB = '    '

atexit.register(lambda: shutil.rmtree(MODIFICATIONS_DIR))

os.environ['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'  # Disable pip version check


def print_stage(stage):
    print(f"{Fore.CYAN}{'=' * 5} {stage} {'=' * 5}{Fore.RESET}", flush=True)
    time.sleep(.1)


def run_poetry_replacers(line):
    if line.startswith('python = '):
        return 'python = "^3.9"'
    if 'poetry.dev-dependencies' in line:
        return line.replace('poetry.dev-dependencies', 'poetry.group.dev.dependencies')
    return line


def remove_from(line, *imports):
    _, module, _, sub_modules_line = line.split(' ', 3)
    sub_modules = [
        stripped
        for sub_module in sub_modules_line.split(',')
        if (stripped := sub_module.strip()) not in imports
    ]
    return f'from {module} import {", ".join(sub_modules)}'


def run_import_replacers(line):
    if 'dataclasses' in line:
        return remove_from(line, 'KW_ONLY')

    return line


class WaitNicely:
    def __init__(self, start_message, end_message):
        self.start_message = start_message
        self.end_message = end_message
        self.sr = SlashR(False)

    def __enter__(self):
        self.sr.__enter__()
        self.sr.print(f'{Fore.YELLOW}{self.start_message}{Fore.RESET}')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sr.print(f'{Fore.GREEN}{self.end_message} ✔{Fore.RESET}')
        self.sr.__exit__(exc_type, exc_val, exc_tb)


class OpenModify:
    def __init__(self, file):
        self.file = file
        filename = file.replace(MODIFICATIONS_DIR, '').lstrip(os.path.sep)
        self.wait_nicely = WaitNicely(f"Modifying {filename}", f"Modified {filename}")
        with open(file, 'r') as f:
            self.old_data = f.read()

    def __enter__(self):
        self.f = open(self.file, 'w')
        self.wait_nicely.__enter__()
        return self.f, self.old_data

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.f.close()
        self.wait_nicely.__exit__(exc_type, exc_val, exc_tb)


# ========================================
print_stage("Clone the rmscene repo")
# ========================================
os.makedirs(CACHE_DIR, exist_ok=True)
if not os.path.exists(REPO_CLONE_DIR):
    subprocess.run(["git", "clone", REPO_URL, REPO_CLONE_DIR], stderr=subprocess.STDOUT)
else:
    subprocess.run(["git", "-C", REPO_CLONE_DIR, 'fetch', '--all'], stderr=subprocess.STDOUT)
    subprocess.run(["git", "-C", REPO_CLONE_DIR, 'reset', '--hard', 'origin/main'], stderr=subprocess.STDOUT)
os.chdir(MODIFICATIONS_DIR)

# ========================================
print_stage("Setup the environment")
# ========================================
with WaitNicely("Creating virtual environment", f"Created virtual environment"):
    if not os.path.exists(PYTHON_EXECUTABLE) and not os.path.exists(PIP_EXECUTABLE):
        if os.path.exists(VENV_DIR):
            shutil.rmtree(VENV_DIR)
        venv.create(VENV_DIR, with_pip=True)

packages = ' '.join(EXTRA_PACKAGES)
with WaitNicely(f"Installing {packages}", f"Installed {packages}"):
    subprocess.run([PIP_EXECUTABLE, "install", *EXTRA_PACKAGES], stdout=subprocess.PIPE)
shutil.copytree(REPO_CLONE_DIR, MODIFICATIONS_DIR, dirs_exist_ok=True)

# ========================================
print_stage("Running modifications")
# ========================================
with OpenModify(os.path.join(MODIFICATIONS_DIR, "pyproject.toml")) as (f, old):
    f.write('\n'.join(
        run_poetry_replacers(line)
        for line in old.splitlines()
    ))
with OpenModify(os.path.join(SOURCE_DIR, 'tagged_block_reader.py')) as (f, old):
    imports_fixed = '\n'.join(
        run_import_replacers(line)
        for line in old.splitlines()
    )
    classes = []
    lines = (line for line in imports_fixed.splitlines())
    base_args: List[Tuple[str, str, str]] = []
    base_kwargs: List[Tuple[str, str, str]] = []
    while (line := next(lines, None)) is not None:
        class_lines = []
        var_lines = []
        if line.startswith('@dataclass'):
            class_lines.append(line)  # @dataclass
            class_definition = next(lines)
            class_lines.append(class_definition)  # class ...
            while (line := next(lines, None)) is not None:  # Detect tab
                class_lines.append(line)
                if len(line) < 1:
                    line = next(lines)
                    if len(line) < 1:
                        break
                elif not (line.startswith('\t') or line.startswith(' ' * 4)):
                    break
                line_stripped = line.strip()
                if line_stripped.startswith('"') or line_stripped.startswith("#"):
                    continue
                var_lines.append(line_stripped)
        else:
            continue

        class_remade_lines = [
            class_definition
        ]
        args = []
        kwargs = []

        kwarg_only = False
        for var in var_lines:
            var_name, var_type = [part.strip() for part in var.split(':')]
            if '=' in var_type:
                var_type, default = var_type.split('=')
                var_type = var_type.strip()
                default_value = default.strip()
            else:
                default_value = None
            if var_type == 'KW_ONLY':
                kwarg_only = True
                continue
            if kwarg_only:
                kwargs.append((var_name, var_type, default_value))
            else:
                args.append((var_name, var_type, default_value))

        if is_base := class_definition.endswith('BlockInfo:'):
            base_args = args.copy()
            base_kwargs = kwargs.copy()
            args.clear()
            kwargs.clear()

        if not (args or kwargs or is_base):
            continue

        args_code = ', '.join(
            f"{arg_name}: {arg_type} = {default_value}"
            if default_value else f"{arg_name}: {arg_type}"
            for arg_name, arg_type, default_value in (
                *base_args, *args
            )
        )
        kwargs_code = ', '.join(
            f"{kwarg_name}: {kwarg_type} = {default_value}"
            if default_value else f"{kwarg_name}: {kwarg_type}"
            for kwarg_name, kwarg_type, default_value in (
                *base_kwargs, *kwargs
            )
        )
        class_remade_lines.append(f"{TAB}def __init__({args_code}, *, {kwargs_code}):")
        if not is_base:
            base_args_code = ', '.join(arg_name for arg_name, _, _ in base_args)
            base_kwargs_code = ', '.join(f'{kwarg_name} = {kwarg_name}' for kwarg_name, _, _ in base_kwargs)
            class_remade_lines.append(
                f"{TAB}{TAB}super().__init__({base_args_code}, {base_kwargs_code})")
        for var_name, var_type, _ in args + kwargs:
            class_remade_lines.append(f"{TAB}{TAB}self.{var_name}: {var_type} = {var_name}")

        class_code = '\n'.join(class_lines)
        class_remade_code = '\n'.join(class_remade_lines)

        classes.append((class_code, class_remade_code))

    final = imports_fixed
    for class_code, class_remade_code in classes:
        final = final.replace(class_code, class_remade_code)

    f.write(final)

with OpenModify(os.path.join(SOURCE_DIR, 'scene_stream.py')) as (f, old):
    imports_fixed = '\n'.join(
        run_import_replacers(line)
        for line in old.splitlines()
    )
    f.write(imports_fixed)

# ========================================
print_stage("Running tests")
# ========================================
with WaitNicely("Preparing poetry", "Prepared poetry"):
    subprocess.run([PYTHON_EXECUTABLE, "-m", "poetry", "lock"], stdout=subprocess.DEVNULL)
    subprocess.run([PYTHON_EXECUTABLE, "-m", "poetry", "install"], stdout=subprocess.DEVNULL)

with (WaitNicely("Running tests", "Finished running tests")):
    tests_output = subprocess.run([PYTHON_EXECUTABLE, "-m", "poetry", "run", "pytest"], stdout=subprocess.PIPE
                                  ).stdout.decode()

if 'error' in tests_output.lower():
    print(f"{Fore.RED}Tests had some errors{Fore.RESET}")
    print_stage("Please fix the modifications before continuing")
    print(f"{Fore.RED}{tests_output}{Fore.RESET}")
    exit(1)

# ========================================
print_stage("Copy sources...")
# ========================================
shutil.copytree(os.path.join(MODIFICATIONS_DIR, "src/rmscene"), os.path.join(WORK_DIR, "rmscene"), dirs_exist_ok=True)
