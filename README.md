# tg-ws-proxy-android.1.0
fork tg-ws-proxy 22.03.2026

README (RU версия)
# tg-ws-proxy-android

Android-адаптированный форк проекта [Flowseal/tg-ws-proxy](https://github.com/Flowseal/tg-ws-proxy), позволяющий использовать Telegram через WebSocket-туннель с локальным SOCKS5-прокси.

## 📱 Что это

Этот проект запускает локальный SOCKS5-прокси на Android (через Termux):


127.0.0.1:1080


Telegram подключается к нему и весь трафик:
- уходит через WebSocket (WSS)
- при необходимости fallback на TCP

## 🚀 Возможности

- локальный SOCKS5 прокси
- обход блокировок через WebSocket
- автоматическое определение Telegram DC
- fallback на прямое соединение
- логирование
- запуск в Termux

---

## 📦 Установка (Termux)

### 1. Установить базовые пакеты

pkg update && pkg upgrade
pkg install python git rust clang libffi openssl
git clone <YOUR_FORK_URL>
cd tg-ws-proxy-android
pip install -e .
tg-ws-proxy-android init
tg-ws-proxy-android start --wake-lock
tg-ws-proxy-android open

