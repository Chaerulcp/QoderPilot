"""Local, atomic persistence for jobs that still need client login."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Iterable

from .models import PendingJob


class PendingJobStore:
    def __init__(self, path: Path):
        self.path = path

    def read(self) -> list[PendingJob]:
        if not self.path.is_file():
            return []
        jobs: list[PendingJob] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                jobs.append(PendingJob.from_mapping(value))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        return jobs

    def upsert(self, job: PendingJob) -> None:
        jobs = {item.email.casefold(): item for item in self.read()}
        jobs[job.email.casefold()] = job
        self._write(jobs.values())

    def remove(self, email: str) -> None:
        jobs = [item for item in self.read() if item.email.casefold() != email.casefold()]
        self._write(jobs)

    def _write(self, jobs: Iterable[PendingJob]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for job in jobs:
                handle.write(json.dumps(job.as_dict(), ensure_ascii=False) + "\n")
        os.replace(temporary, self.path)
        try:
            self.path.chmod(stat.S_IREAD | stat.S_IWRITE)
        except OSError:
            pass


def count_nonempty_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())



