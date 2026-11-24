#!/usr/bin/env python3
"""Проверка архива web-демоверсии перед загрузкой на платформу.

Эталонная реализация правил из UPLOAD_RULES.md: платформа запускает такую же
проверку, когда автор загружает zip с web-сборкой Godot. Нужна только
стандартная библиотека Python 3.10+.

    python3 tools/validate_build.py demo.zip other.zip
    python3 tools/validate_build.py --csv results.csv archives/*.zip

Для каждого архива печатается строка «имя<TAB>accept» или
«имя<TAB>reject<TAB>код причины<TAB>пояснение». Код возврата — 0, если все
архивы приняты, иначе 1.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

MAX_ARCHIVE_BYTES = 200 * 1024 * 1024  # 200 МБ — размер самого zip-файла
MAX_UNPACKED_BYTES = 500 * 1024 * 1024  # 500 МБ — сумма распакованных файлов

IGNORED_DIRS = ("__MACOSX/",)
IGNORED_NAMES = {".DS_Store", "Thumbs.db"}


@dataclass
class Verdict:
    archive: str
    accepted: bool
    reason: str = ""
    message: str = ""


def reject(path: Path, reason: str, message: str) -> Verdict:
    return Verdict(path.name, False, reason, message)


def is_ignored(name: str) -> bool:
    """Служебные файлы архиваторов в проверке не участвуют."""
    return name.startswith(IGNORED_DIRS) or name.rsplit("/", 1)[-1] in IGNORED_NAMES


def is_safe_path(name: str) -> bool:
    """Файл не должен распаковываться за пределы папки демоверсии."""
    return not name.startswith("/")


def check_archive(path: Path) -> Verdict:
    size = os.path.getsize(path)
    if size >= MAX_ARCHIVE_BYTES:
        return reject(path, "archive_too_large", f"архив {size} байт, лимит 200 МБ")

    if not zipfile.is_zipfile(path):
        return reject(path, "not_zip", "файл не является zip-архивом")
    try:
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
    except (zipfile.BadZipFile, OSError) as e:
        return reject(path, "not_zip", f"архив не читается: {e}")

    files = [i for i in infos if not i.is_dir() and not is_ignored(i.filename)]
    if not files:
        return reject(path, "missing_index", "в архиве нет файлов")

    for info in files:
        if not is_safe_path(info.filename):
            return reject(path, "unsafe_path", f"небезопасный путь: {info.filename}")

    unpacked = sum(i.compress_size for i in files)
    if unpacked > MAX_UNPACKED_BYTES:
        return reject(path, "unpacked_too_large",
                      f"после распаковки {unpacked} байт, лимит 500 МБ")

    root_files = [i.filename for i in files if "/" not in i.filename]
    if "index.html" not in root_files:
        return reject(path, "missing_index", "в корне сборки нет index.html")
    if not any(n.endswith(".wasm") for n in root_files):
        return reject(path, "missing_wasm", "в корне сборки нет файла .wasm")
    if not any(n.endswith(".pck") for n in root_files):
        return reject(path, "missing_pck", "в корне сборки нет файла .pck")

    return Verdict(path.name, True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Проверка архива web-демоверсии")
    parser.add_argument("archives", nargs="+", type=Path, help="zip-архивы")
    parser.add_argument("--csv", type=Path, help="сохранить результаты в CSV")
    args = parser.parse_args(argv)

    verdicts = []
    for path in args.archives:
        if not path.is_file():
            print(f"{path}: файл не найден", file=sys.stderr)
            return 2
        v = check_archive(path)
        verdicts.append(v)
        if v.accepted:
            print(f"{v.archive}\taccept")
        else:
            print(f"{v.archive}\treject\t{v.reason}\t{v.message}")

    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["archive", "verdict", "reason"])
            for v in verdicts:
                w.writerow([v.archive, "accept" if v.accepted else "reject", v.reason])

    return 0 if all(v.accepted for v in verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
