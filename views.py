"""
Модуль views содержит классы для создания пользовательского интерфейса:
  - EnvironmentSelector: универсальный виджет выбора сред.
  - CreateTab: вкладка создания фича‑флагов.
  - DeleteTab: вкладка для удаления фича‑флагов с возможностью множественного удаления.
  - UpdateActivityTab: вкладка для изменения активности фича‑флагов с динамическим добавлением записей.
  - MainWindow: главное окно, содержащее все вкладки.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit,
                             QComboBox, QTextEdit, QPushButton, QMessageBox,
                             QGroupBox, QHBoxLayout, QCheckBox, QTabWidget)
from PyQt5.QtCore import Qt
from workers import EnvWorker, DeleteMultipleWorker, ActivityUpdateWorker


class EnvironmentSelector(QWidget):
    """
    Универсальный виджет для выбора сред.
    Содержит чекбокс ALL и индивидуальные чекбоксы для "dev", "test", "preprod", "stage" и "prod".
    Метод get_selected_envs() возвращает список выбранных сред.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_env_checkbox = QCheckBox("ALL")
        self.all_env_checkbox.stateChanged.connect(self.on_all_env_changed)
        self.env_checkboxes = {}
        layout = QHBoxLayout()
        layout.addWidget(self.all_env_checkbox)
        for env in ["dev", "test", "preprod", "stage", "prod"]:
            cb = QCheckBox(env)
            if env == "prod":
                cb.setStyleSheet("color: red; font-weight: bold;")
            cb.stateChanged.connect(self.individual_env_changed)
            self.env_checkboxes[env] = cb
            layout.addWidget(cb)
        self.setLayout(layout)

    def on_all_env_changed(self, state):
        check = self.all_env_checkbox.isChecked()
        for cb in self.env_checkboxes.values():
            cb.blockSignals(True)
            cb.setChecked(check)
            cb.blockSignals(False)

    def individual_env_changed(self, state):
        all_checked = all(cb.isChecked() for cb in self.env_checkboxes.values())
        self.all_env_checkbox.blockSignals(True)
        self.all_env_checkbox.setChecked(all_checked)
        self.all_env_checkbox.blockSignals(False)

    def get_selected_envs(self):
        return [env for env, cb in self.env_checkboxes.items() if cb.isChecked()]


class CreateTab(QWidget):
    """Вкладка создания фича‑флагов."""

    def __init__(self):
        super().__init__()
        self.workers = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.username_field = QLineEdit()
        self.username_field.setMinimumWidth(200)
        self.username_field.setPlaceholderText("Ivan.Ivanov без @X5.RU")
        form_layout.addRow("Username (Обязательное):", self.username_field)

        self.password_field = QLineEdit()
        self.password_field.setMinimumWidth(200)
        self.password_field.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password (Обязательное):", self.password_field)

        self.id_field = QLineEdit()
        self.id_field.setMinimumWidth(500)
        self.id_field.setPlaceholderText("Команда.Сервис.НазваниеФичи")
        form_layout.addRow("ID (Обязательное):", self.id_field)

        self.description_field = QLineEdit()
        self.description_field.setMinimumWidth(500)
        self.description_field.setPlaceholderText("Описание фичи")
        form_layout.addRow("Description (Обязательное):", self.description_field)

        self.enabled_field = QComboBox()
        self.enabled_field.addItems(["true", "false"])
        self.enabled_field.setCurrentIndex(1)
        form_layout.addRow("Enabled:", self.enabled_field)

        self.team_field = QComboBox()
        self.team_field.addItems([
            "autotest-team", "b2b-united", "delivery-team", "devops-team",
            "pnb-team", "randi-team", "reporting-team", "rnd-team",
            "storebox-team", "tms-team", "ux-team"
        ])
        form_layout.addRow("Team:", self.team_field)

        self.audience_type_field = QComboBox()
        self.audience_type_field.addItems(["ALL", "SERVICE"])
        form_layout.addRow("Audience Type:", self.audience_type_field)

        self.audience_target_field = QLineEdit()
        self.audience_target_field.setMinimumWidth(500)
        self.audience_target_field.setPlaceholderText("Укажите заафекченые сервисы через ','")
        form_layout.addRow("Audience Target (Обязательное):", self.audience_target_field)

        self.taskId_field = QLineEdit()
        self.taskId_field.setText("OMNI-")
        form_layout.addRow("Task ID (Обязательное):", self.taskId_field)

        self.removalFeatureTaskId_field = QLineEdit()
        self.removalFeatureTaskId_field.setMinimumWidth(500)
        self.removalFeatureTaskId_field.setPlaceholderText("Обязательно, если Is Scheduled For Removal = true")
        form_layout.addRow("Removal Feature Task ID:", self.removalFeatureTaskId_field)

        self.isScheduledForRemoval_field = QComboBox()
        self.isScheduledForRemoval_field.addItems(["true", "false"])
        self.isScheduledForRemoval_field.setCurrentIndex(1)
        form_layout.addRow("Is Scheduled For Removal:", self.isScheduledForRemoval_field)

        self.plannedRemovalDate_field = QLineEdit()
        self.plannedRemovalDate_field.setMinimumWidth(500)
        self.plannedRemovalDate_field.setPlaceholderText("Обязательно, если Is Scheduled For Removal = true")
        form_layout.addRow("Planned Removal Date:", self.plannedRemovalDate_field)

        layout.addLayout(form_layout)
        self.env_selector = EnvironmentSelector()
        layout.addWidget(self.env_selector)
        self.submit_button = QPushButton("Создать фича-флаг")
        self.submit_button.clicked.connect(self.submit_action)
        layout.addWidget(self.submit_button)
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)
        self.setLayout(layout)

    def append_result(self, text):
        self.result_area.append(text)
        self.result_area.append("-" * 60)

    def submit_action(self):
        self.result_area.clear()
        feature_id = self.id_field.text().strip()
        description = self.description_field.text().strip()
        enabled_str = self.enabled_field.currentText()
        enabled = True if enabled_str.lower() == "true" else False
        team = self.team_field.currentText()
        audience_type = self.audience_type_field.currentText()
        audience_target_str = self.audience_target_field.text().strip()
        audience_target = [s.strip() for s in audience_target_str.split(",") if s.strip()]
        taskId = self.taskId_field.text().strip()
        removalFeatureTaskId = self.removalFeatureTaskId_field.text().strip()
        isScheduledForRemoval_str = self.isScheduledForRemoval_field.currentText()
        isScheduledForRemoval = True if isScheduledForRemoval_str.lower() == "true" else False
        plannedRemovalDate = self.plannedRemovalDate_field.text().strip()
        username = self.username_field.text().strip()
        password = self.password_field.text().strip()

        missing_fields = []
        if not feature_id:
            missing_fields.append("ID")
        if not description:
            missing_fields.append("Description")
        if not audience_target_str:
            missing_fields.append("Audience Target")
        if not taskId:
            missing_fields.append("Task ID")
        if not username:
            missing_fields.append("Username")
        if not password:
            missing_fields.append("Password")
        if isScheduledForRemoval:
            if not plannedRemovalDate:
                missing_fields.append("Planned Removal Date (Обязательное)")
            if not removalFeatureTaskId:
                missing_fields.append("Removal Feature Task ID (Обязательное)")
        if missing_fields:
            QMessageBox.warning(self, "Input Error",
                                "Пожалуйста, заполните обязательные поля: " + ", ".join(missing_fields))
            return

        feature_payload = {
            "id": feature_id,
            "description": description,
            "enabled": enabled,
            "team": team,
            "audience": {"type": audience_type, "target": audience_target},
            "removalFeatureTaskId": removalFeatureTaskId,
            "isScheduledForRemoval": isScheduledForRemoval,
            "taskId": taskId,
            "plannedRemovalDate": plannedRemovalDate
        }

        selected_envs = self.env_selector.get_selected_envs()
        if not selected_envs:
            QMessageBox.warning(self, "Input Error", "Выберите хотя бы одну среду для выполнения запроса")
            return

        self.workers = []
        for env in selected_envs:
            worker = EnvWorker(env, username, password, feature_payload)
            worker.result_signal.connect(self.append_result)
            self.workers.append(worker)
            worker.start()


class DeleteEntry(QWidget):
    """
    Виджет одного элемента удаления фичи.
    Содержит одно текстовое поле для ввода ID и кнопку для удаления этого элемента.
    """

    def __init__(self, remove_callback, parent=None):
        super().__init__(parent)
        self.remove_callback = remove_callback
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        self.feature_id_edit = QLineEdit()
        self.feature_id_edit.setPlaceholderText("ID фичи")
        layout.addWidget(self.feature_id_edit)
        self.remove_button = QPushButton("X")
        self.remove_button.setFixedWidth(30)
        self.remove_button.clicked.connect(lambda: self.remove_callback(self))
        layout.addWidget(self.remove_button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def get_data(self):
        return self.feature_id_edit.text().strip()


class DeleteTab(QWidget):
    """
    Вкладка для удаления фича‑флагов.
    Содержит поля Username и Password, виджет для выбора сред,
    а также область для динамического добавления записей удаления (каждая запись – поле для ID).
    При нажатии на кнопку Delete отправляется DELETE‑запрос для каждого указанного ID.
    """

    def __init__(self):
        super().__init__()
        self.delete_entries = []
        self.workers = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.username_field = QLineEdit()
        self.username_field.setMinimumWidth(200)
        self.username_field.setPlaceholderText("Ivan.Ivanov без @X5.RU")
        form_layout.addRow("Username (Обязательное):", self.username_field)
        self.password_field = QLineEdit()
        self.password_field.setMinimumWidth(200)
        self.password_field.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password (Обязательное):", self.password_field)
        layout.addLayout(form_layout)
        self.env_selector = EnvironmentSelector()
        layout.addWidget(self.env_selector)
        self.entries_group = QGroupBox("Фичи для удаления:")
        self.entries_layout = QVBoxLayout()
        self.entries_group.setLayout(self.entries_layout)
        layout.addWidget(self.entries_group)
        # Добавляем одно поле по умолчанию:
        self.add_entry()
        self.add_entry_button = QPushButton("+")
        self.add_entry_button.setFixedWidth(30)
        self.add_entry_button.clicked.connect(self.add_entry)
        layout.addWidget(self.add_entry_button, alignment=Qt.AlignLeft)
        self.delete_button = QPushButton("Удалить фича-флаги")
        self.delete_button.clicked.connect(self.submit_action)
        layout.addWidget(self.delete_button)
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)
        self.setLayout(layout)

    def add_entry(self):
        entry = DeleteEntry(self.remove_entry)
        self.delete_entries.append(entry)
        self.entries_layout.addWidget(entry)

    def remove_entry(self, entry):
        if entry in self.delete_entries:
            self.entries_layout.removeWidget(entry)
            entry.deleteLater()
            self.delete_entries.remove(entry)

    def append_result(self, text):
        self.result_area.append(text)
        self.result_area.append("-" * 60)

    def submit_action(self):
        self.result_area.clear()
        username = self.username_field.text().strip()
        password = self.password_field.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Заполните обязательные поля: Username, Password")
            return

        feature_ids = [entry.get_data() for entry in self.delete_entries if entry.get_data()]
        if not feature_ids:
            QMessageBox.warning(self, "Input Error", "Нет добавленных записей для удаления")
            return

        selected_envs = self.env_selector.get_selected_envs()
        if not selected_envs:
            QMessageBox.warning(self, "Input Error", "Выберите хотя бы одну среду для удаления")
            return

        # Подтверждение удаления
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Подтверждение удаления")
        msg_box.setText(f"Вы действительно хотите удалить фича-флаги: {', '.join(feature_ids)}?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        response = msg_box.exec_()

        if response == QMessageBox.No:
            return  # Пользователь нажал "Нет", прерываем операцию

        # Запуск удаления
        self.workers = []
        for env in selected_envs:
            worker = DeleteMultipleWorker(env, username, password, feature_ids)
            worker.result_signal.connect(self.append_result)
            self.workers.append(worker)
            worker.start()


class UpdateActivityEntry(QWidget):
    """
    Виджет одного элемента обновления активности.
    Содержит поле для ввода ID фичи, combobox для выбора enabled, и кнопку удаления элемента.
    """

    def __init__(self, remove_callback, parent=None):
        super().__init__(parent)
        self.remove_callback = remove_callback
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        self.feature_id_edit = QLineEdit()
        self.feature_id_edit.setPlaceholderText("ID фичи")
        layout.addWidget(self.feature_id_edit)
        self.enabled_combo = QComboBox()
        self.enabled_combo.addItems(["true", "false"])
        layout.addWidget(self.enabled_combo)
        self.remove_button = QPushButton("X")
        self.remove_button.setFixedWidth(30)
        self.remove_button.clicked.connect(lambda: self.remove_callback(self))
        layout.addWidget(self.remove_button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def get_data(self):
        return (self.feature_id_edit.text().strip(), self.enabled_combo.currentText().strip())


class UpdateActivityTab(QWidget):
    """
    Вкладка для изменения активности фича‑флагов.
    Содержит поля Username и Password, виджет для выбора сред,
    а также область для динамического добавления записей обновления (каждая запись содержит ID и enabled).
    При нажатии на кнопку Update для каждого выбранного окружения токен запрашивается один раз,
    а затем для каждой записи отправляется PUT‑запрос вида:
         {base_url}/{ID}/enabled/{enabled}
    """

    def __init__(self):
        super().__init__()
        self.update_entries = []
        self.workers = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.username_field = QLineEdit()
        self.username_field.setMinimumWidth(200)
        self.username_field.setPlaceholderText("Ivan.Ivanov без @X5.RU")
        form_layout.addRow("Username (Обязательное):", self.username_field)
        self.password_field = QLineEdit()
        self.password_field.setMinimumWidth(200)
        self.password_field.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password (Обязательное):", self.password_field)
        main_layout.addLayout(form_layout)
        self.env_selector = EnvironmentSelector()
        main_layout.addWidget(self.env_selector)
        self.entries_group = QGroupBox("Фичи для обновления активности:")
        self.entries_layout = QVBoxLayout()
        self.entries_group.setLayout(self.entries_layout)
        main_layout.addWidget(self.entries_group)
        # Добавляем поле по умолчанию
        self.add_entry()
        self.add_entry_button = QPushButton("+")
        self.add_entry_button.setFixedWidth(30)
        self.add_entry_button.clicked.connect(self.add_entry)
        main_layout.addWidget(self.add_entry_button, alignment=Qt.AlignLeft)
        self.update_button = QPushButton("Обновить активность фича-флагов")
        self.update_button.clicked.connect(self.submit_action)
        main_layout.addWidget(self.update_button)
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        main_layout.addWidget(self.result_area)
        self.setLayout(main_layout)

    def add_entry(self):
        entry = UpdateActivityEntry(self.remove_entry)
        self.update_entries.append(entry)
        self.entries_layout.addWidget(entry)

    def remove_entry(self, entry):
        if entry in self.update_entries:
            self.entries_layout.removeWidget(entry)
            entry.deleteLater()
            self.update_entries.remove(entry)

    def append_result(self, text):
        self.result_area.append(text)
        self.result_area.append("-" * 60)

    def submit_action(self):
        self.result_area.clear()
        username = self.username_field.text().strip()
        password = self.password_field.text().strip()

        missing_fields = []
        if not username:
            missing_fields.append("Username")
        if not password:
            missing_fields.append("Password")
        if not self.update_entries:
            missing_fields.append("Нет добавленных записей для обновления")
        else:
            for i, entry in enumerate(self.update_entries, 1):
                feature_id, _ = entry.get_data()
                if not feature_id:
                    missing_fields.append(f"В записи {i} не заполнен ID")

        if missing_fields:
            QMessageBox.warning(self, "Input Error",
                                "Заполните обязательные поля: " + ", ".join(missing_fields))
            return

        update_list = []
        feature_ids = []
        for entry in self.update_entries:
            feature_id, enabled = entry.get_data()
            update_list.append((feature_id, enabled))
            feature_ids.append(feature_id)

        selected_envs = self.env_selector.get_selected_envs()
        if not selected_envs:
            QMessageBox.warning(self, "Input Error", "Выберите хотя бы одну среду для обновления")
            return

        # Подтверждение обновления активности
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Подтверждение обновления активности")
        msg_box.setText(f"Вы действительно хотите обновить активность фича-флагов: {', '.join(feature_ids)}?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        response = msg_box.exec_()

        if response == QMessageBox.No:
            return  # Пользователь нажал "Нет", прерываем операцию

        # Запуск обновления активности
        self.workers = []
        for env in selected_envs:
            worker = ActivityUpdateWorker(env, username, password, update_list)
            worker.result_signal.connect(self.append_result)
            self.workers.append(worker)
            worker.start()


class MainWindow(QTabWidget):
    """
    Главное окно приложения, содержащее вкладки:
      - "Создание" для создания фича‑флагов,
      - "Удаление" для удаления фича‑флагов,
      - "Изменение активности" для обновления активности фича‑флагов.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Feature Toggle Manager")
        self.create_tab = CreateTab()
        self.delete_tab = DeleteTab()
        self.update_tab = UpdateActivityTab()
        self.addTab(self.create_tab, "Создание")
        self.addTab(self.delete_tab, "Удаление")
        self.addTab(self.update_tab, "Изменение активности")
