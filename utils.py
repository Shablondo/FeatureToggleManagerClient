"""
Модуль utils содержит вспомогательные функции проекта.

Функция update_hosts() добавляет в файл hosts запись:
    193.232.108.20 kc-omni.x5.ru
если она ещё не присутствует. Работает для Windows и macOS.
Запуск требует прав администратора.
"""

import platform


def update_hosts():
    """
    Добавляет запись "193.232.108.20 kc-omni.x5.ru" в файл hosts для Windows и macOS,
    если её там ещё нет.

    Пути:
      - Windows: C:\Windows\System32\drivers\etc\hosts
      - macOS: /etc/hosts

    Если запись уже присутствует, функция ничего не делает.
    """
    new_entry = "193.232.108.20 kc-omni.x5.ru"
    system_name = platform.system()
    if system_name == "Windows":
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    elif system_name == "Darwin":
        hosts_path = "/etc/hosts"
    else:
        hosts_path = "/etc/hosts"

    try:
        with open(hosts_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        if any(new_entry in line for line in lines):
            print("Запись уже существует в hosts.")
            return
        with open(hosts_path, "a", encoding="utf-8") as f:
            f.write("\n" + new_entry + "\n")
        print("Запись добавлена в hosts.")
    except Exception as e:
        print(f"Ошибка при обновлении hosts: {e}")
