from unittest import mock

import requests
from django.test import TestCase, override_settings

from core.testing import make_student
from integrations.adapters.cerbrum import CerbrumGradesProvider
from integrations.adapters.moodle import MoodleClient, MoodleCoursesProvider, MoodleMaterialsProvider
from integrations.base import IntegrationUnavailable

MOODLE = {"MOODLE_BASE_URL": "https://moodle.exemplo.br", "MOODLE_TOKEN": "TOKEN-SECRETO-123"}


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status = payload, status

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError("erro com TOKEN-SECRETO-123 na URL")

    def json(self):
        return self.payload


class CerbrumTests(TestCase):
    def test_stub_falha_explicitamente_sem_inventar_dados(self):
        provider = CerbrumGradesProvider()
        self.assertFalse(provider.is_configured())
        with self.assertRaises(IntegrationUnavailable):
            provider.fetch("1")


class MoodleTests(TestCase):
    @override_settings(MOODLE_BASE_URL="", MOODLE_TOKEN="")
    def test_sem_configuracao_levanta_indisponivel(self):
        with self.assertRaises(IntegrationUnavailable):
            MoodleClient()

    @override_settings(**MOODLE)
    def test_disciplinas_mapeadas_para_dto(self):
        payload = [{"id": 7, "shortname": "POO", "fullname": "Programação Orientada a Objetos"}]
        with mock.patch("requests.post", return_value=FakeResponse(payload)) as post:
            courses = MoodleCoursesProvider().fetch("42")
        self.assertEqual(courses[0].code, "POO")
        # o token vai no corpo do POST, nunca na URL
        args, kwargs = post.call_args
        self.assertNotIn("TOKEN-SECRETO-123", args[0])
        self.assertEqual(kwargs["data"]["userid"], "42")

    @override_settings(**MOODLE)
    def test_materiais_percorrem_cursos_e_modulos(self):
        respostas = [
            FakeResponse([{"id": 7, "shortname": "POO"}]),
            FakeResponse([{"modules": [
                {"name": "Slides 1", "url": "https://moodle.exemplo.br/mod/resource/1"},
                {"name": "Rótulo sem link"},
            ]}]),
        ]
        with mock.patch("requests.post", side_effect=respostas):
            materiais = MoodleMaterialsProvider().fetch("42")
        self.assertEqual([m.title for m in materiais], ["Slides 1"])

    @override_settings(**MOODLE)
    def test_falhas_viram_indisponivel_sem_vazar_token(self):
        casos = [
            requests.ConnectionError("TOKEN-SECRETO-123"),
            requests.Timeout("TOKEN-SECRETO-123"),
        ]
        for erro in casos:
            with mock.patch("requests.post", side_effect=erro):
                with self.assertRaises(IntegrationUnavailable) as ctx:
                    MoodleCoursesProvider().fetch("42")
            self.assertNotIn("TOKEN-SECRETO-123", str(ctx.exception))
            self.assertIsNone(ctx.exception.__cause__)

        with mock.patch("requests.post", return_value=FakeResponse({}, status=500)):
            with self.assertRaises(IntegrationUnavailable):
                MoodleCoursesProvider().fetch("42")
        with mock.patch("requests.post", return_value=FakeResponse({"exception": "x", "message": "TOKEN-SECRETO-123"})):
            with self.assertRaises(IntegrationUnavailable) as ctx:
                MoodleCoursesProvider().fetch("42")
        self.assertNotIn("TOKEN-SECRETO-123", str(ctx.exception))
