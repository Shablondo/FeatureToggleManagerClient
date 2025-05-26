"""
Модуль workers содержит классы для выполнения сетевых запросов с использованием QThread из PyQt5.

Содержимое:
  - get_token(): получает Bearer‑токен.
  - BaseWorker: базовый класс для worker‑ов (объединяет получение токена и отправку HTTP‑запросов).
  - EnvWorker: для создания фича‑флага (POST‑запрос).
  - DeleteEnvWorker: для удаления одного фича‑флага (DELETE‑запрос).
  - DeleteMultipleWorker: для удаления нескольких фич (для каждой в списке – DELETE‑запрос).
  - ActivityUpdateWorker: для обновления активности фича‑флагов (PUT‑запросы).
"""

import requests
import urllib3
from PyQt5.QtCore import QThread, pyqtSignal
from config import ENV_CONFIG

# Отключаем предупреждения об SSL сертификатах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_token(envKC, username, password):
    """
    Получает и возвращает Bearer‑токен для указанного окружения.

    :param envKC: ключ окружения ("dev", "test", "preprod", "stage", "prod")
    :param username: имя пользователя для авторизации
    :param password: пароль для авторизации
    :return: токен (str)
    :raises: ValueError, если токен не найден или произошла ошибка HTTP.
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


class BaseWorker(QThread):
    """
    Базовый класс для worker‑ов.
    Содержит общую логику получения токена и отправки HTTP‑запросов.
    """
    result_signal = pyqtSignal(str)

    def __init__(self, envKC, username, password, parent=None):
        super().__init__(parent)
        self.envKC = envKC
        self.username = username
        self.password = password

    def get_token_and_notify(self):
        """
        Получает токен и отправляет уведомление через result_signal.
        :return: токен (str) или None, если произошла ошибка.
        """
        try:
            token = get_token(self.envKC, self.username, self.password)
            self.result_signal.emit(f"[{self.envKC}] Получен токен: {token[:30]}...")
            return token
        except Exception as e:
            self.result_signal.emit(f"[{self.envKC}] Ошибка при получении токена: {str(e)}")
            return None

    def send_request(self, method, url, headers=None, json_data=None):
        """
        Отправляет HTTP‑запрос.
        :param method: "POST", "PUT" или "DELETE"
        :param url: URL запроса
        :param headers: заголовки запроса
        :param json_data: данные для POST/PUT (если применимо)
        :return: ответ (json или текст)
        :raises: исключение, если запрос завершился ошибкой.
        """
        if method == "POST":
            response = requests.post(url, headers=headers, json=json_data, verify=False)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=json_data, verify=False)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, verify=False)
        else:
            raise ValueError("Неподдерживаемый HTTP метод.")
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            return response.text


class EnvWorker(BaseWorker):
    """
    Worker для создания фича‑флага – отправляет POST‑запрос.
    """

    def __init__(self, envKC, username, password, feature_payload, parent=None):
        super().__init__(envKC, username, password, parent)
        self.feature_payload = feature_payload

    def run(self):
        token = self.get_token_and_notify()
        if not token:
            return
        feature_url = ENV_CONFIG[self.envKC]["feature"]
        headers = {
            "accept": "*/*",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        try:
            resp = self.send_request("POST", feature_url, headers=headers, json_data=self.feature_payload)
            self.result_signal.emit(f"[{self.envKC}] Feature создан успешно. Ответ: {resp}")
        except Exception as e:
            self.result_signal.emit(f"[{self.envKC}] Ошибка при создании: {str(e)}")


class DeleteMultipleWorker(BaseWorker):
    """
    Worker для удаления нескольких фича‑флагов.
    Принимает список feature_ids и для каждого отправляет DELETE‑запрос.
    """

    def __init__(self, envKC, username, password, feature_ids, parent=None):
        super().__init__(envKC, username, password, parent)
        self.feature_ids = feature_ids

    def run(self):
        token = self.get_token_and_notify()
        if not token:
            return
        base_url = ENV_CONFIG[self.envKC]["feature"]
        for feature_id in self.feature_ids:
            delete_url = f"{base_url}/{feature_id}"
            headers = {"accept": "*/*", "Authorization": f"Bearer {token}"}
            try:
                resp = self.send_request("DELETE", delete_url, headers=headers)
                self.result_signal.emit(f"[{self.envKC}] Фича с id '{feature_id}' успешно удалена. Ответ: {resp}")
            except Exception as e:
                self.result_signal.emit(f"[{self.envKC}] Ошибка при удалении фичи '{feature_id}': {str(e)}")


class ActivityUpdateWorker(BaseWorker):
    """
    Worker для обновления активности фича‑флагов.
    Для каждого обновления из update_list (список кортежей (feature_id, enabled))
    отправляется PUT‑запрос вида: {base_url}/{feature_id}/enabled/{enabled}
    """

    def __init__(self, envKC, username, password, update_list, parent=None):
        super().__init__(envKC, username, password, parent)
        self.update_list = update_list

    def run(self):
        token = self.get_token_and_notify()
        if not token:
            return
        base_url = ENV_CONFIG[self.envKC]["feature"]
        for feature_id, enabled in self.update_list:
            update_url = f"{base_url}/{feature_id}/enabled/{enabled}"
            headers = {
                "accept": "*/*",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            try:
                resp = self.send_request("PUT", update_url, headers=headers)
                self.result_signal.emit(
                    f"[{self.envKC}] Обновление активности фичи '{feature_id}' на '{enabled}' успешно. Ответ: {resp}")
            except Exception as e:
                self.result_signal.emit(f"[{self.envKC}] Ошибка при обновлении фичи '{feature_id}': {str(e)}")
