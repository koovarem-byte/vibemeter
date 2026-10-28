# Стикеры

Основные — эмодзи из пака [VibemeterNeon](https://t.me/addemoji/VibemeterNeon)
(`stickers.PACK`: 💎 девушкам, 👑 парням «VIP на 7 дней», 💜 мэтч). Если Telegram
не примет эмодзи стикером, бот шлёт эти запасные файлы:

- `sticker_2_vip_girls.webp` — VIP девушкам (после анкеты и рассылка девушкам)
- `sticker_3_vip_7days.webp` — рассылка парням «за 3 подруги VIP на 7 дней»
- `sticker_5_match.webp` — взаимный вайб

Перерисовать: `python3 assets/stickers/make_stickers.py`. Свои картинки — просто
заменить файлы (512×512 webp) и убрать имя из `stickers.PACK`.
Удачный `file_id` бот хранит в `app_state` (`sticker_<имя>`).
