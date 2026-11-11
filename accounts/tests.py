from django.core.cache import cache
from rest_framework.test import APITestCase

from core.testing import PASSWORD, make_student

from .models import User


class AuthTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.student = make_student("20260001", first="Ana", last="Souza")

    def _login(self, password=PASSWORD):
        return self.client.post("/api/auth/login/", {"username": "20260001", "password": password})

    def test_login_valido_retorna_tokens(self):
        resp = self._login()
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_invalido_retorna_401(self):
        self.assertEqual(self._login("errada").status_code, 401)

    def test_me_sem_token_retorna_401(self):
        self.assertEqual(self.client.get("/api/me/").status_code, 401)

    def test_me_retorna_somente_o_proprio_usuario(self):
        make_student("20260002")
        access = self._login().data["access"]
        resp = self.client.get("/api/me/", HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["username"], "20260001")
        self.assertEqual(resp.data["student"]["registration_number"], "20260001")

    def test_logout_invalida_o_refresh_token(self):
        refresh = self._login().data["refresh"]
        self.assertEqual(self.client.post("/api/auth/logout/", {"refresh": refresh}).status_code, 200)
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": refresh}).status_code, 401)

    def test_superusuario_recebe_perfil_admin(self):
        su = User.objects.create_superuser(username="root", password="x" * 12)
        self.assertEqual(su.role, User.Role.ADMIN)

    def test_limite_de_tentativas_de_login(self):
        codes = [self._login("errada").status_code for _ in range(25)]
        self.assertIn(429, codes)
