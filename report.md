# Отчёт по практической работе №2: окружения и зависимости Python

## 1. Окружение и версии

- ОС: Microsoft Windows NT 10.0.26200.0
- Python: 3.12.7 (CPython)
- Poetry: 2.5.1
- pip: 24.2

Poetry установлен через `install.python-poetry.org`, бинарник в
`C:\Users\User\AppData\Roaming\Python\Scripts`. В PATH добавлял через
`setx PATH "$Env:Path;C:\Users\User\AppData\Roaming\Python\Scripts"`,
после этого команда `poetry` заработала. Из-за предупреждения `setx` про
усечение до 1024 знаков PATH пришлось применять дважды — второй раз
сработал.

## 2. Пути к интерпретаторам

**pip_project:**
```

C:\CodeMonkey\5 sem\mlops\2\mlops-2-kovalev\practice_2_result\pip_project.venv\Scripts\python.exe

```

**poetry_project:**
```

C:\CodeMonkey\5 sem\mlops\2\mlops-2-kovalev\practice_2_result\poetry_project.venv\Scripts\python.exe

```

Оба — Python 3.12.7, CPython. Проверял через
`python -c "import sys; print(sys.executable)"` (pip_project) и
`poetry env info --path` / `poetry env info --executable` (poetry_project).

## 3. Прямые зависимости

В обоих проектах одинаковые:

- `requests` — HTTP-запрос к Open-Meteo.
- `matplotlib` — построение графика.
- `pandas` — DataFrame с временем и температурой.

Для Poetry дополнительно:

- `pytest` (группа `test`) — тесты функции `build_dataframe`.
- `ruff` (группа `dev`) — линтер.

`numpy` **не** прямая зависимость: в `plt_temp.py` он не импортируется.
Приходит транзитивно — `pip show pandas` показывает
`Requires: numpy, python-dateutil, tzdata`, а `pip show numpy` —
`Required-by: contourpy, matplotlib, pandas`.

## 4. Транзитивные зависимости (по одной на каждый основной пакет)

По `poetry show --tree`:

- `requests` → `urllib3` (`urllib3 >=1.26,<3`)
- `matplotlib` → `contourpy` (`contourpy >=1.0.1`, тянет `numpy >=2.0`)
- `pandas` → `python-dateutil` (`>=2.8.2`, тянет `six >=1.5`)

## 5. Восстановление pip_project

Последовательность:

```

python -m pip freeze > requirements.txt
deactivate
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
..venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

```

На первом прогоне `pip install` упал с
`SSLError DECRYPTION_FAILED_OR_BAD_RECORD_MAC` на pypi.org. Повторный
запуск прошёл — все 18 пакетов установились из кэша, версии совпали с
`requirements.txt` (`certifi==2026.7.22`, `requests==2.34.2`,
`pandas==3.0.6`, `matplotlib==3.11.2`, `numpy==2.5.3` и т.д.).

Сам скрипт `python plt_temp.py` при этом падает с `ConnectTimeout` к
`api.open-meteo.com`. Проблема сетевая (то же самое было и в
poetry_project), не связана с восстановлением окружения.
`python -m pip show numpy` в новом окружении отрабатывает — окружение
собралось корректно.

## 6. Проверка групп Poetry

**`poetry install --only main`**

- выбрана группа main
- pytest — недоступен (`"pytest" не является внутренней или внешней
  командой`)
- ruff — недоступен
- основной скрипт запускается: падает только на сетевом запросе, не на
  импортах
- причина: `--only main` ставит только основную группу, группы `test`
  и `dev` игнорируются.

**`poetry install --only test`**

- выбрана группа `test`
- pytest — доступен, но собрал 0 тестов и упал на
  `ModuleNotFoundError: No module named 'pandas'` (сами тесты импортируют
  pandas, а он в main)
- ruff — недоступен
- основной скрипт падает с `ModuleNotFoundError: No module named
  'requests'`
- причина: `--only test` ставит только тестовую группу, основная
  игнорируется.

**`poetry install` (полное окружение)**

- доступны и pytest, и ruff
- `poetry run pytest` → 4 passed
- `poetry run ruff check .` → нашёл 2 ошибки I001 (несортированные
  импорты в `plt_temp.py`), обе fixable через `--fix`
- `poetry run python plt_temp.py` → падает на `ConnectTimeout` к
  Open-Meteo, не на импортах

После эксперимента окружение восстановлено `poetry install`.

## 7. Точечное обновление зависимости

`poetry show --outdated` не показал устаревших пакетов — все прямые
зависимости уже на последних версиях в своих диапазонах.

Ограничение `requests` изменил с `^2.34.2` (эквивалент
`>=2.34.2,<3.0.0`) на явное `>=2.31,<3.0`:

```

poetry add "requests@>=2.31,<3.0"
poetry lock
poetry update requests

```

`git diff pyproject.toml` показал:
```

- "requests (>=2.34.2,<3.0.0)",

- "requests (>=2.31,<3.0)",

```

`git diff poetry.lock` показал единственное изменение — `content-hash`
(пересчитался из-за правки `pyproject.toml`). Версия `requests` осталась
`2.34.2`, транзитивные зависимости (`urllib3`, `certifi`,
`charset-normalizer`, `idna`) — на тех же версиях.

Ответы на вопросы задания:

1. **Изменилось ли ограничение прямой зависимости?** Да — нижняя граница
   опустилась с 2.34.2 до 2.31, верхняя граница осталась `<3.0` (запрет
   на мажорную версию 3.x).
2. **Изменилась ли установленная версия?** Нет, `requests` уже был на
   2.34.2 и остался на 2.34.2 — более новых совместимых версий нет.
3. **Какие транзитивные зависимости изменились?** Никакие. В `poetry.lock`
   поменялся только `content-hash`.
4. **Почему обновление не выходит за диапазон?** Solver подбирает версии
   строго в пределах `>=2.31,<3.0`, которые заданы в `pyproject.toml`.
   Как только решение упрётся в границу `<3.0`, Poetry не предложит
   `3.x`. Верхняя граница защищает от мажорных обновлений с ломающими
   изменениями.

Отсутствие более новых совместимых версий — не ошибка, а нормальный
результат: `poetry update requests` отработал «No dependencies to install
or update».

## 8. Экспорт и чистое восстановление Poetry-проекта

Плагин экспорта (`poetry-plugin-export`) на момент проверки не был
установлен — `poetry self show plugins` ничего не вывел. Поставил:

```

poetry self add poetry-plugin-export

```

Установилась версия 1.10.1. Затем:

```

poetry export --format requirements.txt --output requirements.txt

```

Файл получился с хешами (`--hash=sha256:...`) для каждого пакета —
это особенность `poetry export`, удобно для `pip install --require-hashes`.

Чистое восстановление окружения Poetry:

```

Remove-Item -Recurse -Force .venv
Test-Path .venv          # False
poetry env use 3.12
poetry install

```

Создался `.venv` внутри `poetry_project`, установились 24 пакета строго
по `poetry.lock`. Poetry попутно ругнулся:

```

Error: The current project could not be installed: No file/folder found
for package poetry-project

```

Это потому, что в `pyproject.toml` не выставлен `package-mode = false`,
а отдельного пакета `poetry-project/` в дереве нет — Poetry пытается
поставить корневой проект и не находит его. На работу окружения это не
влияет: зависимости встали, `poetry run` подхватывает `.venv` проекта.

Проверки после восстановления:

- `poetry run pytest` → 4 passed (за 0.75 с, без сети)
- `poetry run ruff check .` → работает (2 замечания I001, не критичны)
- `poetry run python plt_temp.py` → падает на `ConnectTimeout` к
  Open-Meteo, не на импортах

Сетевой доступ к `api.open-meteo.com` из этой сети не работает:
`ConnectTimeout` и `SSLError DECRYPTION_FAILED_OR_BAD_RECORD_MAC`. Это не
связано с окружениями; тесты, которые не ходят в сеть, проходят
нормально — что и требовалось по заданию (тест должен проверять функцию
преобразования без обращения к API).

## 9. Сравнение venv+pip и Poetry

**venv + pip:**
Воспроизводимость держится на `requirements.txt`, снятом через
`pip freeze`. В файле лежат точные версии всех установленных пакетов —
и прямых, и транзитивных. Восстановление — `pip install -r
requirements.txt` в новом venv. Минус: `freeze` не различает, какие
пакеты нужны проекту самому, а какие притащились как зависимости. Групп
нет, lock-файла нет.

**Poetry:**
Воспроизводимость держится на паре `pyproject.toml` + `poetry.lock`.
`pyproject.toml` описывает намерения (прямые зависимости, диапазоны,
группы, версию Python), `poetry.lock` — конкретное решение solver'а со
всеми транзитивными пакетами и хешами. `poetry install` поднимает ровно
то, что в lock. Плюс встроенные группы (`main` / `test` / `dev`),
`poetry run` без ручной активации, `poetry show --tree` для разбора
дерева, `poetry add` / `remove` для изменения зависимостей.

В обоих случаях настоящая проверка воспроизводимости — удалить `.venv`
и собрать заново. У pip_project это делается через `pip install -r
requirements.txt`, у poetry_project — через `poetry install`.

## 10. Что не добавлял в Git

В `.gitignore` обоих проектов:

```

.venv/
**pycache**/
*.py[cod]
.pytest_cache/
.ruff_cache/
temperature_24h.csv
temperature_24h.png

```

В Git попали: `plt_temp.py`, `requirements.txt` (у pip_project),
`pyproject.toml`, `poetry.lock`, `poetry.toml`, `conftest.py`,
`tests/test_dataframe.py` (у poetry_project), `.gitignore`, `report.md`.

`.venv` и кэши не коммитил — при `git add .` они не попали, потому что
`.gitignore` их отсекает.

## 11. Прочее (грабли по ходу работы)

- Poetry изначально не был в PATH — поставился в
  `C:\Users\User\AppData\Roaming\Python\Scripts`, но текущая сессия
  PowerShell его не видела. Помогло `setx` + повторный запуск команды.
- Однажды активированное `.venv` из `pip_project` подхватывалось
  Poetry-командами в `poetry_project` — в логе было видно
  `pytest -- ... pip_project\.venv\Scripts\python.exe`. После
  `deactivate` Poetry стал использовать своё окружение.
- Тесты сначала падали с `ModuleNotFoundError: No module named
  'plt_temp'`. Помогло: `deactivate` чужого venv + `poetry env use 3.12`
  + `poetry install`. После этого `sys.path` при `pytest` уже включал
  корень проекта, и `from plt_temp import build_dataframe` заработал.
- Команда `deactivate` в PowerShell работает только когда есть активное
  venv-окружение. Если оно уже снято — команда не найдётся, это нормально.