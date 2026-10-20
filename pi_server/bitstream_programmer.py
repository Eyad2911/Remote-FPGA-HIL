import os
import subprocess
from typing import Callable, Optional


class BitstreamError(Exception):
    pass


class BitstreamProgrammer:
    _MIN_VALID_SIZE = 4
    _BOARD = "basys3"

    def program(self, filepath: str, progress_callback: Optional[Callable[[int], None]] = None) -> None:
        if not os.path.isfile(filepath):
            raise BitstreamError(f"Bitstream file not found: {filepath!r}")
        file_size = os.path.getsize(filepath)
        if file_size < self._MIN_VALID_SIZE:
            raise BitstreamError(
                f"File {filepath!r} is too small ({file_size} bytes) to be a valid bitstream."
            )

        if progress_callback:
            progress_callback(0)

        result = subprocess.run(
            ["openFPGALoader", "-b", self._BOARD, filepath],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise BitstreamError(f"openFPGALoader failed (exit {result.returncode}): {detail}")

        if progress_callback:
            progress_callback(100)
