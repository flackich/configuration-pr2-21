# Практическая работа № 2 — вариант 21

**Дисциплина:** Конфигурационное управление, РТУ МИРЭА.

Инструмент исследования графа зависимостей пакетов JavaScript (npm).
Внешние библиотеки и npm как источник зависимостей не используются:
данные читаются непосредственно из npm registry.

## Этап 1 — CLI и конфигурация

Реализован интерфейс командной строки и валидация всех параметров:

- `--package` — имя пакета;
- `--repository` — URL npm registry либо путь к тестовому JSON;
- `--test-mode` — использовать тестовый репозиторий;
- `--max-depth` — максимальная глубина анализа (целое >= 0);
- `--exclude` — подстрока для исключения пакетов.

Только на первом этапе программа выводит настройки в формате ключ-значение.
Обрабатываются отсутствующие аргументы, неверные имена, URL, пути и глубина.

## Запуск

Python 3.10+, сторонние Python-библиотеки не требуются.

```sh
./run.sh --package is-odd --repository https://registry.npmjs.org
```

На Windows:

```bat
run.bat --package is-odd --repository https://registry.npmjs.org
```

## Тесты

```sh
python3 -m unittest discover -s tests -v
```

## Этапы в Git

Каждый этап оформлен отдельным Conventional/Scoped Commit.

## Этап 2 — прямые зависимости npm

Добавлен клиент npm registry (`src/registry.py`). Программа делает HTTP-запрос
к адресу `https://registry.npmjs.org/<package>`, сама разбирает JSON и читает
поле `dependencies` выбранной версии (по умолчанию тег `latest`).
Ни `npm`, ни сторонние библиотеки для извлечения зависимостей не используются.

```sh
./run.sh --package is-odd --repository https://registry.npmjs.org
```

На этом этапе выводятся только **прямые** зависимости. Поддержаны типичные
семантические диапазоны версий: `^`, `~`, `>=`, `<`, `x`, `*`, `||`.
Нестандартные протоколы версий явно отвергаются.

## Этап 3 — транзитивный граф и тестовый режим

Добавлен алгоритм **DFS без рекурсии** (явный стек) в `src/graph.py`.
Он получает транзитивные зависимости с ограничением `--max-depth`,
исключает пакеты с указанной подстрокой `--exclude` и выявляет циклы.
Пакеты npm обозначаются как `имя@версия`, поскольку одному имени могут
соответствовать разные разрешённые версии.

Тестовый режим использует JSON вида `{ "A": ["B", "C"], "B": [] }`.
Названия пакетов — только заглавные латинские буквы, как в методичке.

```sh
./run.sh --package A --repository test_data/simple.json --test-mode --max-depth 3
./run.sh --package A --repository test_data/cycle.json --test-mode --max-depth 5
./run.sh --package A --repository test_data/deep.json --test-mode --max-depth 2 --exclude C
```

Присутствуют тесты простого, циклического, глубокого и пустого графов.
При обходе хранится минимальная уже обработанная глубина вершины:
это позволяет корректно ограничивать глубину даже при нескольких путях
к одному и тому же пакету.

## Этап 4 — порядок загрузки

Метод `dependency_first_order()` (`src/order.py`) выдаёт **детерминированный
топологический порядок** обхода: сначала зависимости, затем зависящий пакет.
Реализация использует итеративный DFS. Если есть цикл, программа не выдаёт
ложный порядок, а сообщает, что топологическая сортировка невозможна.

```sh
./run.sh --package A --repository test_data/simple.json --test-mode --max-depth 4
```

### Сопоставление с настоящим npm

Штатная команда `npm ls --all` показывает дерево фактически установленных
пакетов, а `npm view <package> dependencies --json` — прямые зависимости.
**npm не определяет универсальный порядок установки**, поэтому наш
топологический порядок является допустимым порядком по графу, но не
предсказанием внутреннего планирования npm. Сценарий `scripts/compare_with_npm.sh` и результаты проверки
в [COMPARISON.md](COMPARISON.md) доступны с этого этапа.

## Этап 5 — визуализация D2

Граф преобразуется в текстовое описание на языке D2 (`src/d2.py`).
Зависимости обозначаются направленными стрелками: `"A" -> "B"` означает,
что A зависит от B. Описание выводится в терминал. Дополнительно:

- `--only-d2` — напечатать только D2 для перенаправления в файл;
- `--output output/graph.d2` — записать D2-описание в файл.

```sh
./run.sh --package A --repository test_data/simple.json --test-mode --max-depth 4
./run.sh --package A --repository test_data/simple.json --test-mode \
  --max-depth 4 --only-d2 --output output/simple.d2
```

### Демонстрация трёх разных пакетов

```sh
./scripts/demo_three_packages.sh
```

Сценарий анализирует `is-number`, `is-odd`, `is-even`, формирует D2 для каждого
и сохраняет его в `output/`. Нужен доступ к `registry.npmjs.org`.

### Сравнение со штатными инструментами npm

```sh
./scripts/compare_with_npm.sh is-odd
./scripts/compare_with_npm.sh is-even
./scripts/compare_with_npm.sh is-number
```

Этот сценарий сначала запускает **наш** анализатор, затем отдельно выполняет
`npm view ... dependencies --json` и `npm ls --all` в изолированном
временном каталоге. `npm install` вызывается только в сравнительном сценарии,
с выключенными install-скриптами; **наш инструмент npm не использует**.
Результаты могут отличаться, поскольку:

- анализатор строит собственный граф выбранных версий без lockfile;
- npm устанавливает дерево с дедупликацией и может использовать lockfile;
- сейчас анализируется поле `dependencies` (не `devDependencies`, `peerDependencies`
  и `optionalDependencies`), а npm может учитывать дополнительные категории;
- npm не гарантирует единственный порядок фактической установки;
- реализован документированный поднабор npm semver, а не полный стандарт;
- спецпротоколы (`file:`, `git+`, `workspace:`) не поддержаны и вызывают ошибку.

### Структура проекта

```text
src/              исходный код (CLI, registry, semver, DFS, order, D2)
tests/            автоматические модульные тесты
scripts/          сценарии демонстрации и сравнения с npm
test_data/        тестовые репозитории (простой, цикл, глубокий, пустой)
run.sh            запуск macOS/Linux
run.bat           запуск Windows
README.md         инструкция и объяснение ограничений
.gitignore        исключает временные и сгенерированные файлы
```

### История этапов

1. `feat(cli): add validated command-line configuration`
2. `feat(npm): retrieve direct dependencies from npm registry`
3. `feat(graph): implement iterative DFS with depth and cycle checks`
4. `feat(order): add dependency-first topological traversal`
5. `feat(d2): generate D2 dependency graph visualization`

Для показа конкретного этапа на защите:

```sh
git log --oneline --reverse -- .
git checkout <hash-from-log>
python3 -m unittest discover -s tests -v
./run.sh --help
git switch main
```

**На Windows:** для показа коммитов используйте `git checkout <hash>`,
а для запуска — `run.bat`, для тестирования — `py -3 -m unittest discover -s tests -v`.

### Публикация на GitHub с сохранением всех пяти коммитов

Сначала распакуйте скачанный ZIP **с папкой `.git`**. Откройте терминал
в корне проекта. Понадобятся Git и GitHub CLI (`gh`) с авторизацией.

```sh
gh auth login
./scripts/publish_github.sh
```

Скрипт создаёт **новый публичный** репозиторий
`configuration-pr2-21` в вашем аккаунте и отправляет в него ветку `main`
со всеми пятью коммитами. Репозиторий практической №1 не изменяется.

Если вы заранее создали пустой репозиторий на GitHub, вместо скрипта:

```sh
git remote add origin https://github.com/ВАШ_ЛОГИН/configuration-pr2-21.git
git push -u origin main
```

Не копируйте проект без `.git`, иначе история из пяти коммитов потеряется.

## Проверенные примеры

В папке [examples](examples) сохранены D2-графы трёх настоящих пакетов. Результаты сравнения с npm приведены в [COMPARISON.md](COMPARISON.md). Все пять этапов проверены отдельно: 4, 6, 11, 14 и 18 тестов соответственно.
