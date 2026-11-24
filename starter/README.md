# Стартовый проект

| Путь | Что это |
|---|---|
| `game/` | пустой проект Godot 4.4: рендерер Compatibility (нужен для Web), действия ввода `move_left` / `move_right` / `move_up` / `move_down` (WASD и стрелки), `jump` (пробел), `action` (J), `restart` (R), пресет экспорта **Web без потоков** |
| `UPLOAD_RULES.md` | правила, по которым платформа принимает или отклоняет архив с демоверсией |
| `tools/validate_build.py` | эталонный валидатор архива по этим правилам, только стандартная библиотека Python 3.10+ |
| `archives/manifest.example.csv` | пример формата манифеста тестовых архивов |
| `.gitignore` | не даёт закоммитить `.godot/`, сборку и сгенерированные архивы |

## Web-сборка

Установите шаблоны экспорта (Editor → Manage Export Templates), затем:

```bash
cd game
godot --headless --path . --import          # первый раз после клона, создаёт .godot/
mkdir -p build/web                          # Godot не создаёт папку сам
godot --headless --path . --export-release "Web" build/web/index.html
python3 -m http.server -d build/web 8000    # открыть http://localhost:8000
```

Сборка без потоков запускается на обычном статическом сервере, на itch.io и GitHub Pages без особых заголовков. Открыть `index.html` двойным щелчком не получится: браузер не загрузит `.wasm` по `file://`.

Архив для платформы — содержимое папки `build/web`:

```bash
cd build/web && zip -r ../../../my_demo.zip . && cd -
```

## Валидатор

```bash
python3 tools/validate_build.py my_demo.zip
python3 tools/validate_build.py --csv results.csv archives/*.zip
```

Что коммитить: всё, кроме `.godot/`, папки сборки и сгенерированных архивов. Файлы `*.import` и `*.uid` (их создаёт Godot 4.4) нужно коммитить.
