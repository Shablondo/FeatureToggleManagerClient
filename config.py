"""
Конфигурация для Feature Toggle Manager Client.

В данном файле определён глобальный словарь ENV_CONFIG, содержащий URL-адреса
для каждой поддерживаемой среды. Для каждой среды задаются:
  - token: адрес для получения Bearer-токена авторизации.
  - feature: базовый адрес для операций с фича‑флагами (создание, удаление).
"""

ENV_CONFIG = {
    "dev": {
         "token": "https://kc-dev-omni.x5.ru/auth/realms/feature-toggle-management-tf/protocol/openid-connect/token",
         "feature": "https://feature-toggle-management-pp-dev.k8s.5post-stage-2.salt.x5.ru/api/v1/feature"
    },
    "test": {
         "token": "https://kc-test-omni.x5.ru/auth/realms/feature-toggle-management-tf/protocol/openid-connect/token",
         "feature": "https://feature-toggle-management-pp-test.k8s.5post-stage-2.salt.x5.ru/api/v1/feature"
    },
    "preprod": {
         "token": "https://kc-preprod-omni.x5.ru/auth/realms/feature-toggle-management-tf/protocol/openid-connect/token",
         "feature": "https://feature-toggle-management.k8s.5post-stage-2.salt.x5.ru/api/v1/feature"
    },
    "stage": {
         "token": "https://kc-stage-omni.x5.ru/auth/realms/feature-toggle-management-tf/protocol/openid-connect/token",
         "feature": "https://feature-toggle-management.k8s.5post-stage-1.salt.x5.ru/api/v1/feature"
    },
    "prod": {
         "token": "https://kc-omni.x5.ru/auth/realms/feature-toggle-management-tf/protocol/openid-connect/token",
         "feature": "https://feature-toggle-management-pp-prod.k8s.5post-stage-2.salt.x5.ru/api/v1/feature"
    }
}
