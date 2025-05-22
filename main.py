"""
Точка входа в проект Feature Toggle Manager Client.
Перед запуском основного окна обновляет файл hosts (если требуется).
"""

import sys
from PyQt5.QtWidgets import QApplication
from views import MainWindow
from utils import update_hosts

if __name__ == "__main__":
    # Попытка обновить файл hosts.
    # Для успешного выполнения может потребоваться запуск с правами администратора.
    update_hosts()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
