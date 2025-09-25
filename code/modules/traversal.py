import asyncio
import os
from pathlib import Path
from typing import Callable

class AsyncDirectoryWalker:
    def __init__(self, root_folder: str, file_callback: Callable, logger):
        self.root_folder = Path(root_folder)
        self.file_callback = file_callback
        self.logger = logger

    async def walk(self):
        await self._walk_folder(self.root_folder)

    async def _walk_folder(self, folder: Path):
        self.logger.info(f"Entering folder: {folder}")
        try:
            for entry in os.scandir(folder):
                path = Path(entry.path)
                if entry.is_dir(follow_symlinks=False):
                    await self._walk_folder(path)
                elif entry.is_file(follow_symlinks=False):
                    await self.file_callback(path)
        except Exception as e:
            self.logger.error(f"Error traversing {folder}: {e}")