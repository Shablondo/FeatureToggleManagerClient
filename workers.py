# workers.py
"""
Модуль workers содержит классы для выполнения сетевых запросов
с использованием QThread из PyQt5. Здесь реализованы:
  - EnvWorker: для создания фича‑флагов (POST-запрос).
  - DeleteEnvWorker: для удаления фича‑флагов (DELETE-запрос).
Общая логика получения токена вынесена в функцию get_token.
"""

import requests
import urllib3
from PyQt5.QtCore import QThread, pyqtSignal
from config import ENV_CONFIG

# Отключаем предупреждения об SSL сертификатах (только для разработки)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_token(envKC, username, password):
    """
    Получает токен для выбранного окружения.

    Параметры:
      envKC (str): ключ окружения ("dev", "test", "preprod", "stage", "prod")
      username (str): имя пользователя для авторизации
      password (str): пароль для авторизации

    Возвращает:
      str: токен, если успешно, или None в случае ошибки.

    Также функция генерирует исключение, если происходит ошибка HTTP.
    """
    urls = ENV_CONFIG.get(envKC)
    if not urls:
        raise ValueError(f"Окружение {envKC} не настроено в ENV_CONFIG.")
    token_url = urls["token"]
    token_payload = {
        "client_id": "feature-service",
        "username": username,
        "grant_type": "password",
        "password": password
    }
    response = requests.post(
        token_url,
        data=token_payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        verify=False
    )
    response.raise_for_status()
    token_json = response.json()
    token = token_json.get("access_token")
    if not token:
        raise ValueError(f"[{envKC}] Не найден access_token в ответе.")
    return token

class EnvWorker(QThread):
    """
    Выполняет POST-запрос для создания фича‑флага.

    Атрибуты:
      envKC (str): выбранное окружение
      username (str): имя пользователя
      password (str): пароль
      feature_payload (dict): данные операции (JSON) для отправки
    """
    result_signal = pyqtSignal(str)

    def __init__(self, envKC, username, password, feature_payload, parent=None):
        super().__init__(parent)
        self.envKC = envKC
        self.username = username
        self.password = password
        self.feature_payload = feature_payload

    def run(self):
        try:
            token = get_token(self.envKC, self.username, self.password)
            self.result_signal.emit(f"[{self.envKC}] Получен токен: {token[:30]}...")
        except Exception as e:
            self.result_signal.emit(f"[{self.envKC}] Ошибка при получении токена: {str(e)}")
            return

        # Получаем URL для операции создания
        feature_url = ENV_CONFIG[self.envKC]["feature"]
        try:
            headers = {
                "accept": "*/*",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            feature_response = requests.post(
                feature_url,
                headers=headers,
                json=self.feature_payload,
                verify=False
            )
            feature_response.raise_for_status()
            try:
                resp_json = feature_response.json()
            except Exception:
                resp_json = feature_response.text
            self.result_signal.emit(f"[{self.envKC}] Feature создан успешно. Ответ: {resp_json}")
        except Exception as e:
            self.result_signal.emit(f"[{self.envKC}] Ошибка при создании: {str(e)}")

class DeleteEnvWorker(QThread):
    """
    Выполняет DELETE-запрос для удаления фича‑флага.

    Атрибуты:
      envKC (str): выбранное окружение
      feature_id (str): ID фичи (будет добавлен к базовому URL)
      username (str): имя пользователя
      password (str): пароль
    """
    result_signal = pyqtSignal(str)

    def __init__(self, envKC, feature_id, username, password, parent=None):
        super().__init__(parent)
        self.envKC = envKC
        self.feature_id = feature_id
        self.username = username
        self.password = password

    def run(self):
        try:
            token = get_token(self.envKC, self.username, self.password)
            self.result_signal.emit(f"[{self.envKC}] Получен токен: {token[:30]}...")
        except Exception as e:
            self.result_signal.emit(f"[{self.envKC}] Ошибка при получении токена: {str(e)}")
            return

        # Формируем URL для удаления, добавляя ID к базовому URL
        base_url = ENV_CONFIG[self.envKC]["feature"]
        delete_url = f"{base_url}/{self.feature_id}"
        try:
            headers = {
                "accept": "*/*",
                "Authorization": f"Bearer {token}"
            }
            delete_response = requests.delete(
                delete_url,
                headers=headers,
                verify=False
            )
            delete_response.raise_for_status()
            self.result_signal.emit(f"[{self.envKC}] Фича с id '{self.feature_id}' успешно удалена.")
        except Exception as e:
            self.result_signal.emit(f"[{self.envKC}] Ошибка при удалении: {str(e)}")
