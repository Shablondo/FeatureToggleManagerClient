"""
Модуль views содержит классы для создания пользовательского интерфейса
приложения Feature Toggle Manager Client:
  - CreateTab: вкладка для создания фича‑флагов.
  - DeleteTab: вкладка для удаления фича‑флагов.
  - MainWindow: главное окно, содержащее вкладки с интерфейсами создания и удаления.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit,
                             QComboBox, QTextEdit, QPushButton, QMessageBox,
                             QGroupBox, QHBoxLayout, QCheckBox, QTabWidget)
from workers import EnvWorker, DeleteEnvWorker

class CreateTab(QWidget):
    """
    Вкладка создания фича‑флагов. Содержит форму ввода всех необходимых полей
    и область для вывода результатов. Также реализована логика выбора сред.
    """
    def __init__(self):
        super().__init__()
        self.workers = []  # Список активных потоков
        self.init_ui()

    def init_ui(self):
        """
        Инициализация интерфейса вкладки создания.
        """
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Поля ввода
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
        self.enabled_field.setCurrentIndex(1)  # false по умолчанию
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
        form_layout.addRow("Removal Feature Task ID", self.removalFeatureTaskId_field)

        self.isScheduledForRemoval_field = QComboBox()
        self.isScheduledForRemoval_field.addItems(["true", "false"])
        self.isScheduledForRemoval_field.setCurrentIndex(1)  # false по умолчанию
        form_layout.addRow("Is Scheduled For Removal:", self.isScheduledForRemoval_field)

        self.plannedRemovalDate_field = QLineEdit()
        self.plannedRemovalDate_field.setMinimumWidth(500)
        self.plannedRemovalDate_field.setPlaceholderText("Обязательно, если Is Scheduled For Removal = true")
        form_layout.addRow("Planned Removal Date", self.plannedRemovalDate_field)

        self.username_field = QLineEdit()
        self.username_field.setMinimumWidth(500)
        self.username_field.setPlaceholderText("Ivan.Ivanov без @X5.RU")
        form_layout.addRow("Username (Обязательное):", self.username_field)

        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password (Обязательное):", self.password_field)

        layout.addLayout(form_layout)

        # Группа для выбора сред выполнения запроса
        self.env_group_box = QGroupBox("Выберите среды выполнения запроса")
        env_layout = QHBoxLayout()
        self.all_env_checkbox = QCheckBox("ALL")
        self.all_env_checkbox.stateChanged.connect(self.on_all_env_changed)
        env_layout.addWidget(self.all_env_checkbox)
        self.env_checkboxes = {}
        for env in ["dev", "test", "preprod", "stage", "prod"]:
            cb = QCheckBox(env)
            if env == "prod":
                cb.setStyleSheet("color: red; font-weight: bold;")
            cb.stateChanged.connect(self.individual_env_changed)
            self.env_checkboxes[env] = cb
            env_layout.addWidget(cb)
        self.env_group_box.setLayout(env_layout)
        layout.addWidget(self.env_group_box)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_action)
        layout.addWidget(self.submit_button)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        self.setLayout(layout)

    def on_all_env_changed(self, state):
        """
        Обрабатывает изменение состояния чекбокса ALL — устанавливает всем индивидуальные чекбоксы выбранное состояние.
        """
        check = self.all_env_checkbox.isChecked()
        for cb in self.env_checkboxes.values():
            cb.blockSignals(True)
            cb.setChecked(check)
            cb.blockSignals(False)

    def individual_env_changed(self, state):
        """
        Если изменение произошло с индивидуальным чекбоксом, обновляет состояние чекбокса ALL.
        """
        all_checked = all(cb.isChecked() for cb in self.env_checkboxes.values())
        self.all_env_checkbox.blockSignals(True)
        self.all_env_checkbox.setChecked(all_checked)
        self.all_env_checkbox.blockSignals(False)

    def append_result(self, text):
        """
        Добавляет строку с результатом в текстовое поле.
        """
        self.result_area.append(text)
        self.result_area.append("-" * 60)

    def submit_action(self):
        """
        Собирает данные из всех полей формы, выполняет валидацию обязательных полей и запускает потоки для выполнения POST-запросов.
        """
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
            QMessageBox.warning(
                self, "Input Error",
                "Пожалуйста, заполните обязательные поля: " + ", ".join(missing_fields)
            )
            return

        feature_payload = {
            "id": feature_id,
            "description": description,
            "enabled": enabled,
            "team": team,
            "audience": {
                "type": audience_type,
                "target": audience_target
            },
            "removalFeatureTaskId": removalFeatureTaskId,
            "isScheduledForRemoval": isScheduledForRemoval,
            "taskId": taskId,
            "plannedRemovalDate": plannedRemovalDate
        }

        selected_envs = [env for env, cb in self.env_checkboxes.items() if cb.isChecked()]
        if not selected_envs:
            QMessageBox.warning(self, "Input Error", "Выберите хотя бы одну среду для выполнения запроса")
            return

        self.workers = []
        for env in selected_envs:
            worker = EnvWorker(env, username, password, feature_payload)
            worker.result_signal.connect(self.append_result)
            self.workers.append(worker)
            worker.start()

class DeleteTab(QWidget):
    """
    Вкладка удаления фича‑флагов. Содержит минимальный набор полей для идентификации фичи,
    а также чекбоксы для выбора сред, для которых будет выполнен DELETE‑запрос.
    """
    def __init__(self):
        super().__init__()
        self.workers = []
        self.init_ui()

    def init_ui(self):
        """
        Инициализация интерфейса вкладки удаления.
        """
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.id_field = QLineEdit()
        self.id_field.setMinimumWidth(300)
        self.id_field.setPlaceholderText("Команда.Сервис.НазваниеФичи")
        form_layout.addRow("ID (Обязательное):", self.id_field)

        self.username_field = QLineEdit()
        self.username_field.setMinimumWidth(300)
        self.username_field.setPlaceholderText("Ivan.Ivanov без @X5.RU")
        form_layout.addRow("Username (Обязательное):", self.username_field)

        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password (Обязательное):", self.password_field)

        layout.addLayout(form_layout)

        self.env_group_box = QGroupBox("Выберите среды удаления")
        env_layout = QHBoxLayout()
        self.all_env_checkbox = QCheckBox("ALL")
        self.all_env_checkbox.stateChanged.connect(self.on_all_env_changed)
        env_layout.addWidget(self.all_env_checkbox)
        self.env_checkboxes = {}
        for env in ["dev", "test", "preprod", "stage", "prod"]:
            cb = QCheckBox(env)
            if env == "prod":
                cb.setStyleSheet("color: red; font-weight: bold;")
            cb.stateChanged.connect(self.individual_env_changed)
            self.env_checkboxes[env] = cb
            env_layout.addWidget(cb)
        self.env_group_box.setLayout(env_layout)
        layout.addWidget(self.env_group_box)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.submit_action)
        layout.addWidget(self.delete_button)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        self.setLayout(layout)

    def on_all_env_changed(self, state):
        """
        Обработчик для чекбокса ALL: ставит или снимает отметку со всех индивидуальных чекбоксов.
        """
        check = self.all_env_checkbox.isChecked()
        for cb in self.env_checkboxes.values():
            cb.blockSignals(True)
            cb.setChecked(check)
            cb.blockSignals(False)

    def individual_env_changed(self, state):
        """
        Обновляет состояние ALL в зависимости от индивидуальных чекбоксов.
        """
        all_checked = all(cb.isChecked() for cb in self.env_checkboxes.values())
        self.all_env_checkbox.blockSignals(True)
        self.all_env_checkbox.setChecked(all_checked)
        self.all_env_checkbox.blockSignals(False)

    def append_result(self, text):
        """
        Добавляет результат операции в область вывода.
        """
        self.result_area.append(text)
        self.result_area.append("-" * 60)

    def submit_action(self):
        """
        Собирает данные из формы и запускает DELETE-запросы для удаления фича‑флага
        во всех выбранных средах.
        """
        self.result_area.clear()
        feature_id = self.id_field.text().strip()
        username = self.username_field.text().strip()
        password = self.password_field.text().strip()

        missing_fields = []
        if not feature_id:
            missing_fields.append("ID")
        if not username:
            missing_fields.append("Username")
        if not password:
            missing_fields.append("Password")
        if missing_fields:
            QMessageBox.warning(self, "Input Error",
                                "Заполните обязательные поля: " + ", ".join(missing_fields))
            return

        selected_envs = [env for env, cb in self.env_checkboxes.items() if cb.isChecked()]
        if not selected_envs:
            QMessageBox.warning(self, "Input Error", "Выберите хотя бы одну среду для удаления")
            return

        self.workers = []
        for env in selected_envs:
            worker = DeleteEnvWorker(env, feature_id, username, password)
            worker.result_signal.connect(self.append_result)
            self.workers.append(worker)
            worker.start()

class MainWindow(QTabWidget):
    """
    Главное окно приложения, содержащее две вкладки:
      - "Создание" для создания фича‑флагов,
      - "Удаление" для удаления фича‑флагов.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Feature Toggle Manager")
        self.create_tab = CreateTab()
        self.delete_tab = DeleteTab()
        self.addTab(self.create_tab, "Создание")
        self.addTab(self.delete_tab, "Удаление")
