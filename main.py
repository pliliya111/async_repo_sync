"""
Gitea downloader.

Скрипт асинхронно, в 3 одновременных задачи, загружает содержимое удаленного git-репозитория,
сохраняет его во временную папку и подсчитывает хэш каждого файла.
"""
import asyncio
import hashlib
import os
import tempfile

import aiofiles
import git

REPO_URL: str = 'https://gitea.radium.group/radium/project-configuration.git'


async def calculate_hash(file_path: str) -> tuple[str, str]:
    """
    Вычисляет SHA256 хэш файла.

    Args:
        file_path (str): Путь к файлу.

    Returns:
        tuple: Кортеж, содержащий путь к файлу и его SHA256 хэш.
    """
    sha256 = hashlib.sha256()
    async with aiofiles.open(file_path, 'rb') as fl:
        while True:
            chunk = await fl.read(1024)
            if not chunk:
                break
            sha256.update(chunk)
    return file_path, sha256.hexdigest()


async def save_result(result_rows: list[str]) -> None:
    """
    Асинхронно сохраняет строки результата в файл.

    Открывает файл 'result.txt' в режиме записи и записывает в него
    все строки, переданные в виде списка result_rows.

    Args:
        result_rows (list of str): Список строк, которые необходимо
                                   записать в файл.

    """
    async with aiofiles.open('result.txt', 'w') as result_file:
        await result_file.writelines(result_rows)


def clone_repository(tempdir: str) -> None:
    """
    Клонирует репозиторий в указанную временную директорию.

    Args:
        tempdir (str): Путь к временной директории.
    """
    git.Repo.clone_from(REPO_URL, tempdir, depth=1, no_checkout=True)


async def gather_tasks(tempdir: str) -> list:
    """
    Создает задачи для вычисления хэшей всех файлов в указанной директории.

    Args:
        tempdir (str): Путь к временной директории.

    Returns:
        list: Список задач для вычисления SHA256 хэшей файлов.
    """
    return [
        calculate_hash(os.path.join(root, fl))
        for root, _, files in os.walk(tempdir)
        for fl in files
    ]


async def run_tasks(tasks: list) -> list:
    """
    Выполняет задачи с использованием семафора.

    Args:
        tasks (list): Список задач для выполнения.

    Returns:
        list: Список результатов выполнения задач.
    """
    sem = asyncio.Semaphore(3)
    async with sem:
        result_tasks = await asyncio.gather(*tasks)
    return result_tasks


async def hash_all_files(tempdir: str) -> list:
    """
    Вычисляет SHA256 хэши всех файлов в указанной директории.

    Args:
        tempdir (str): Путь к временной директории.

    Returns:
        list: Список кортежей (путь к файлу, SHA256 хэш).
    """
    tasks = await gather_tasks(tempdir)
    return await run_tasks(tasks)


async def main() -> None:
    """Основная функция."""
    result_rows = []
    with tempfile.TemporaryDirectory() as tempdir:
        clone_repository(tempdir)
        result_tasks = await hash_all_files(tempdir)

        for file_path_result, file_hash in result_tasks:
            result_rows.append('{0}:{1}\n'.format(file_path_result, file_hash))

        await save_result(result_rows)


if __name__ == '__main__':
    asyncio.run(main())
