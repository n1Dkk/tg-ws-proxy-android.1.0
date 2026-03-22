# TG WS Proxy Android (Termux fork)

Android-oriented fork of [Flowseal/tg-ws-proxy](https://github.com/Flowseal/tg-ws-proxy) for running the local SOCKS5 -> WebSocket bridge inside **Termux** instead of desktop tray apps.

## Что это такое

Оригинальный проект — это локальный SOCKS5-прокси для Telegram, который поднимается на `127.0.0.1`, определяет Telegram DC, уводит трафик в `wss://.../apiws` и при необходимости откатывается на прямой TCP. В upstream-репозитории готовы desktop-обвязки под Windows, macOS и Linux, а основное ядро находится в `proxy/tg_ws_proxy.py`.

Этот fork меняет именно оболочку вокруг ядра:

- убран упор на tray/GUI;
- добавлен Android/Termux launcher `android.py`;
- добавлены примеры для `termux-services` и `Termux:Boot`;
- README переписан под Telegram Android;
- упаковка `pyproject.toml` упрощена под Android/Termux-сценарий.

## Почему именно Termux, а не APK

Ядро проекта уже написано на Python и хорошо подходит для CLI-сервиса. Полноценный APK потребовал бы отдельного Android service layer, foreground notification, lifecycle-обвязки, deep-link integration и нормальной фоновой политики. Для быстрого рабочего форка самый реалистичный путь — **Termux-first**. Что нужно для native APK, расписано в [`docs/NATIVE_APK_ROADMAP.md`](docs/NATIVE_APK_ROADMAP.md).

## Что осталось от upstream без изменений

- логика SOCKS5 / MTProto / WebSocket-моста в `proxy/tg_ws_proxy.py`;
- поддержка fallback на TCP;
- парсинг `--dc-ip`;
- патч init-пакета для mobile clients, где `dc_id` может приходить некорректным.

## Быстрый старт в Termux

### 1. Подготовка окружения

```bash
pkg update && pkg upgrade
pkg install python git rust clang libffi openssl
```

> `cryptography` — нативная зависимость. На части Termux-окружений ей нужен toolchain для сборки.

### 2. Клонирование и установка

```bash
git clone <YOUR_FORK_URL>
cd tg-ws-proxy-android
pip install -e .
```

### 3. Создать дефолтный конфиг

```bash
tg-ws-proxy-android init
```

Это создаст:

- `~/.config/tg-ws-proxy-android/config.json`
- `~/.config/tg-ws-proxy-android/proxy.log`

### 4. Запуск

```bash
tg-ws-proxy-android start --wake-lock
```

### 5. Открыть Telegram с локальным SOCKS5

```bash
tg-ws-proxy-android open
```

Если deep link не откроется автоматически, настрой вручную:

- тип: **SOCKS5**
- сервер: `127.0.0.1`
- порт: `1080`
- логин / пароль: пусто

## Команды launcher'а

```bash
tg-ws-proxy-android init
tg-ws-proxy-android start
tg-ws-proxy-android start --wake-lock -v
tg-ws-proxy-android open
tg-ws-proxy-android show-config
tg-ws-proxy-android paths
```

## Конфиг

Файл: `~/.config/tg-ws-proxy-android/config.json`

```json
{
  "port": 1080,
  "host": "127.0.0.1",
  "dc_ip": [
    "2:149.154.167.220",
    "4:149.154.167.220"
  ],
  "verbose": false,
  "log_max_mb": 5,
  "log_backups": 1,
  "buf_kb": 256,
  "pool_size": 4,
  "wake_lock": false
}
```

## termux-services

Установить поддержку сервисов:

```bash
pkg install termux-services
```

Дальше можно использовать готовый runit-script из `contrib/termux-services/tg-ws-proxy-android/run`.

Самый простой вариант установки:

```bash
bash contrib/install-termux-service.sh
sv up tg-ws-proxy-android
```

Логи runit будут в:

```bash
$PREFIX/var/log/sv/tg-ws-proxy-android/current
```

## Автозапуск после перезагрузки

Есть пример для `Termux:Boot`:

- `contrib/termux-boot/start-tg-ws-proxy-android-direct.sh`

Его можно скопировать в `~/.termux/boot/` и сделать исполняемым.

## Ограничения Android-версии

1. Это **не native APK**, а Termux service/CLI fork.
2. На агрессивных прошивках Android фоновые процессы могут выгружаться без wakelock и видимого Termux notification.
3. На части устройств придется исключить Termux из battery optimization.
4. Calls / voice routing у Telegram через локальный SOCKS5 могут вести себя иначе, чем обычные чаты и медиа.

## Проверка работы

После запуска в логе должны появиться строки вида:

```text
Telegram WS Bridge Proxy
Listening on   127.0.0.1:1080
Configure Telegram client:
SOCKS5 proxy -> 127.0.0.1:1080
```

Потом в Telegram добавляешь SOCKS5 на `127.0.0.1:1080` и смотришь, идут ли соединения в лог.

## Структура форка

```text
android.py                               Android/Termux launcher
proxy/tg_ws_proxy.py                     upstream core
contrib/install-termux-service.sh        helper для runit
contrib/termux-services/.../run          готовый runit script
contrib/termux-boot/...                  пример автозапуска
docs/ANDROID_PORT_NOTES.md               краткий обзор изменений
docs/NATIVE_APK_ROADMAP.md               что нужно для полноценного APK
```

## Лицензия

Сохраняется upstream-лицензия MIT: [LICENSE](LICENSE)
