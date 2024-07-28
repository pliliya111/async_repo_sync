"""Фикстуры для тестирования."""
import asyncio
import os
import tempfile
from typing import Callable
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def temp_file():
    """Фикстура для создания и удаления временного файла."""
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(b'test content')
    temp_file.close()
    yield temp_file.name
    os.remove(temp_file.name)


@pytest.fixture()
def mock_task():
    """Фикстура для создания MagicMock."""
    return MagicMock()


async def test_task(task_id: int, mock_task: MagicMock) -> int:
    """Асинхронная тестовая задача."""
    await asyncio.sleep(0.1)
    mock_task(task_id)
    return task_id


@pytest.fixture()
def test_task_factory(mock_task: MagicMock):
    """Фикстура для создания асинхронной тестовой задачи."""

    async def factory(task_id: int):
        return await test_task(task_id, mock_task)

    return factory


@pytest.fixture()
def active_tasks():
    """Фикстура для отслеживания активных задач."""
    return [0]


async def monitored_task(
    task_id: int, active_tasks: list[int], sem: asyncio.Semaphore,
) -> int:
    """Асинхронная мониторируемая задача."""
    async with sem:
        active_tasks[0] += 1
        await asyncio.sleep(0.1)
        active_tasks[0] -= 1
    return task_id


@pytest.fixture()
def monitored_task_factory(
    active_tasks: list[int],
) -> Callable[[int], asyncio.Future]:
    """Фикстура для создания асинхронной мониторируемой задачи."""
    sem = asyncio.Semaphore(3)
    return lambda task: monitored_task(task, active_tasks, sem)
