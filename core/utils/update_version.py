"""
╔═════════════════════════════╗
║        Bump Version         ║
╚═════════════════════════════╝
"""

import re
import sys
import os

def get_version_file_path():
    """Retorna o caminho absoluto para o arquivo version.py."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "version.py"))


def read_version(file_path=None):
    """Lê a versão atual do arquivo version.py."""
    if file_path is None:
        file_path = get_version_file_path()
    with open(file_path, "r") as f:
        content = f.read()
    match = re.search(r"__version__ = ['\"](\d+\.\d+\.\d+)['\"]", content)
    return match.group(1) if match else None


def write_version(new_version, file_path=None):
    """Atualiza a versão no arquivo version.py."""
    if file_path is None:
        file_path = get_version_file_path()
    with open(file_path, "r") as f:
        content = f.read()
    updated_content = re.sub(r"__version__ = ['\"](\d+\.\d+\.\d+)['\"]", f"__version__ = '{new_version}'", content)
    with open(file_path, "w") as f:
        f.write(updated_content)


def increment_version(version, part="patch"):
    """Incrementa a versão baseada na parte especificada: major, minor ou patch."""
    major, minor, patch = map(int, version.split("."))
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    return f"{major}.{minor}.{patch}"


def main():
    """Verifica a mensagem do commit e atualiza a versão."""
    if len(sys.argv) < 2:
        print("Erro: O caminho para o arquivo de mensagem do commit não foi fornecido.")
        sys.exit(1)

    commit_msg_file = sys.argv[1]

    with open(commit_msg_file, "r") as f:
        commit_message = f.read().strip()

    if "feat" in commit_message:
        part = "minor"
    elif "fix" in commit_message or "custom" in commit_message:
        part = "patch"
    elif "BREAKING CHANGE" in commit_message:
        part = "major"
    elif any(keyword in commit_message for keyword in
             ["docs", "style", "refact", "perf", "test", "chore", "build", "ci", "revert"]):
        part = "patch"
    else:
        print("Nenhum incremento de versão necessário.")
        return

    current_version = read_version()
    if current_version:
        new_version = increment_version(current_version, part)
        write_version(new_version)
        print(f"Versão atualizada de {current_version} para {new_version}")
    else:
        print("Erro: Não foi possível encontrar a versão atual.")


if __name__ == "__main__":
    main()