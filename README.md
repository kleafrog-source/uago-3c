
# UAGO-3C  
## Universal Adaptive Geometric Observer – Three-Cycle Core

> **Анализ геометрических структур через инварианты, а не метки.**  
> UAGO-3C автоматически извлекает фрактальные и топологические инварианты из изображений, генерирует минимальную генеративную формулу и проверяет её через рекурсивное воплощение.

---

## 📋 Overview / Обзор

UAGO-3C implements a three-cycle autonomous discovery pipeline:  
**Discovery → Embodiment → Validation**.  
The system does **not recognize objects** (e.g., “leaf” or “sponge”) — it uncovers the **mathematical essence** that generates the observed pattern.

UAGO-3C реализует трёхцикловой автономный процесс открытия:  
**Открытие → Воплощение → Валидация**.  
Система **не распознаёт объекты** (например, «лист» или «губка») — она раскрывает **математическую сущность**, порождающую наблюдаемый паттерн.

---

## 🚀 Features / Возможности

- **Automatic invariant measurement**: fractal dimension, symmetry, branching, connectivity  
  **Автоматическое измерение инвариантов**: фрактальная размерность, симметрия, ветвление, связность
- **Deterministic formula generation** for 10+ fractal types (Sierpinski, Koch, Menger, Julia, Dragon, etc.)  
  **Детерминированная генерация формул** для 10+ типов фракталов (Сьерпинского, Коха, Менгера, Жюлиа, Дракона и др.)
- **Optional refinement via Mistral AI API**  
  **Опциональное уточнение через Mistral AI API**
- **Interactive JSXGraph visualizations** (self-contained HTML)  
  **Интерактивная визуализация через JSXGraph** (самодостаточный HTML)
- **Closed-loop validation**: regenerated formula is tested for consistency  
  **Замкнутая проверка**: формула проверяется на устойчивость при рекурсивном воплощении

---

## 🔧 Mistral API (Optional) / Mistral API (Опционально)

Mistral API can **refine** the rule-based formula. It is **not required**.

Mistral API может **уточнить** формулу, сгенерированную по правилам. **Не обязателен**.

### Setup / Настройка:
1. Get an API key at [Mistral AI](https://mistral.ai/)
2. Create `.env` in the project root:
   ```env
   MISTRAL_API_KEY=your_key_here
   ```
3. Enable in `config/uago_config.json`:
   ```json
   {
     "use_mistral_api": true,
     "mistral_model": "mistral-large-latest"
   }
   ```

> ⚠️ If the API fails or is disabled, UAGO-3C **automatically falls back** to its local rule-based system.  
> ⚠️ При ошибке или отключении API система **автоматически переключается** на локальную генерацию.

---

## ⚙️ Installation / Установка

```bash
git clone https://github.com/kleafrog-source/uago-3c.git
cd uago-3c
pip install -r requirements.txt
```

> ❗ **Julia is NOT required** — the system uses `procs=0` in PySR to force Python backend.  
> ❗ **Julia НЕ требуется** — система использует `procs=0` в PySR, чтобы работать на Python-бэкенде.

---

## 🏃‍♂️ Usage / Использование
<<<<<<< HEAD

```bash
python main.py path/to/your/image.jpg
```

Output:
- `output/visualizations/attempt_*.html` — interactive visualizations
- `output/reports/latest.json` — full analysis report

Результат:
- `output/visualizations/attempt_*.html` — интерактивные визуализации
- `output/reports/latest.json` — полный отчёт анализа

---

## 📁 Project Structure / Структура проекта

```
<<<<<<< HEAD
uago-3c/
├── main.py                  # Entry point
├── config/uago_config.json  # Configuration
├── src/
│   ├── __init__.py
│   ├── uago_core.py         # Main engine (3-cycle logic)
│   ├── invariant_measurer.py # Fractal & topological invariants
│   ├── symbolic_regressor.py # Formula generation (rule-based + Mistral)
│   └── jsx_visualizer.py    # JSXGraph HTML generator
├── output/
│   ├── visualizations/      # Generated HTML files
│   └── reports/             # JSON analysis reports
└── requirements.txt
=======
  uago-3c/
    ├── src/
    │   ├── uago_core.py         # Основной движок
    ├── symbolic_regressor.py # Генерация формул
    │   ├── invariant_measurer.py # Анализ инвариантов
    │   └── jsx_visualizer.py    # Визуализация
    ├── config/
    │   └── uago_config.json     # Конфигурация
    ├── data/
    │   └── samples/             # Примеры изображений
    ├── output/
    │   ├── visualizations/      # Сохраненные визуализации
    │   └── reports/             # Отчеты анализа
    └── main.py
      README.md # 
=======
>>>>>>> 1693ef006d2f9b98291896ed83087e270c7f7a9f

```bash
python main.py path/to/your/image.jpg
```
>>>>>>> 9339d94a743389ba7949af3a5297195502da8c0e

<<<<<<< HEAD
=======
Output:
- `output/visualizations/attempt_*.html` — interactive visualizations
- `output/reports/latest.json` — full analysis report

Результат:
- `output/visualizations/attempt_*.html` — интерактивные визуализации
- `output/reports/latest.json` — полный отчёт анализа

---

## 📁 Project Structure / Структура проекта

```
uago-3c/
├── main.py                  # Entry point
├── config/uago_config.json  # Configuration
├── src/
│   ├── __init__.py
│   ├── uago_core.py         # Main engine (3-cycle logic)
│   ├── invariant_measurer.py # Fractal & topological invariants
│   ├── symbolic_regressor.py # Formula generation (rule-based + Mistral)
│   └── jsx_visualizer.py    # JSXGraph HTML generator
├── output/
│   ├── visualizations/      # Generated HTML files
│   └── reports/             # JSON analysis reports
└── requirements.txt

>>>>>>> 1693ef006d2f9b98291896ed83087e270c7f7a9f



## 🤝 Contributing / Вклад

Pull requests and bug reports are welcome.

Приветствуются пул-реквесты и сообщения об ошибках.

---

## 📄 License / Лицензия

MIT

<<<<<<< HEAD

<<<<<<< HEAD

=======
1. В файле [symbolic_regressor.py]/symbolic_regressor.py:0:0-0:0) в функции [_generate_with_mistral()]/src/symbolic_regressor.py:40:0-101:18):
   - Формируется промпт с геометрическими инвариантами
   - Отправляется запрос к API Mistral
   - Обрабатывается ответ и извлекается формула

2. В основном цикле обработки (в [uago_core.py](uago_core.py:0:0-0:0)) при включенной опции `use_mistral_api`:
   - Если API ключ указан и доступен, используется Mistral для генерации формул
   - В случае ошибки или отсутствия ключа автоматически переключается на локальную регрессию

3. В конфигурационном файле можно управлять:
   - Включением/отключением API
   - Выбором модели Mistral
   - Настройками таймаутов и других параметров запроса
>>>>>>> 9339d94a743389ba7949af3a5297195502da8c0e
=======
git commit -m "Initial commit: Add UAGO-3C project files"

>>>>>>> 1693ef006d2f9b98291896ed83087e270c7f7a9f
