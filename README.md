# Как освещаются улицы Краснодарского края

Интерактивная карта населённых пунктов: площадь круга — численность населения, длина светящегося кольца — доля освещённых улиц (%).

## Сайт

После публикации: **https://dorozhnij.github.io/krasnodar-street-lighting/**

## Локально

```bash
pip install llmaps pandas
python prepare_data.py
python build_map.py
python -m http.server 8765
# http://127.0.0.1:8765/
```

## Данные

Исходный CSV не входит в репозиторий; в репозитории лежит подготовленный `data/points.geojson` (1179 точек с координатами).

## Стек

[LLMaps](https://github.com/greadr71/LLMaps), MapLibre GL, подложка [OpenFreeMap](https://openfreemap.org/) Dark (без API-ключа).
