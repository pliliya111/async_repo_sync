"""Модуль тестирования."""
import hashlib
import tempfile
from typing import Awaitable, Callable
from unittest.mock import MagicMock, patch

import pytest

from main import REPO_URL, calculate_hash, clone_repository, run_tasks


@pytest.mark.asyncio()
async def test_calculate_hash(temp_file: MagicMock):
    """Тест вычисления хэша файла."""
    sha256 = hashlib.sha256()
    sha256.update(b'test content')
    expected_hash = sha256.hexdigest()

    file_path, file_hash = await calculate_hash(temp_file)

    assert file_path == temp_file
    assert file_hash == expected_hash


@patch('git.Repo.clone_from')
def test_clone_repository(mock_clone_from: MagicMock):
    with tempfile.TemporaryDirectory() as tempdir:
        clone_repository(tempdir)
        mock_clone_from.assert_called_once_with(
            REPO_URL, tempdir, depth=1, no_checkout=True,
        )


@pytest.mark.asyncio()
async def test_run_tasks(
    test_task_factory: Callable[[int], Awaitable[int]],
    mock_task: MagicMock,
    monitored_task_factory: Callable[[int], Awaitable[int]],
    active_tasks: list,
) -> None:
    tasks = [test_task_factory(task_id) for task_id in range(5)]
    task_results = await run_tasks(tasks)
    assert task_results == [0, 1, 2, 3, 4]
    assert mock_task.call_count == 5

    monitored_tasks = [monitored_task_factory(tsk) for tsk in range(10)]
    await run_tasks(monitored_tasks)
    assert active_tasks[0] <= 3
