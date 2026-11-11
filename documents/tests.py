from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from core.models import AuditLog
from core.testing import PDF_BYTES, PrivateMediaMixin, make_secretary, make_student

from .models import DocumentRequest, DocumentType


def pdf(name="x.pdf", content=PDF_BYTES):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


class DocumentFlowBase(PrivateMediaMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.ana = make_student("20260001", first="Ana")
        self.bruno = make_student("20260002", first="Bruno")
        self.secretaria = make_secretary()
        self.tipo = DocumentType.objects.create(
            name="Declaração de matrícula", required_fields=["finalidade"]
        )

    def criar(self, user, finalidade="Estágio"):
        self.client.force_authenticate(user)
        return self.client.post(
            "/api/documentos/solicitacoes/",
            {"document_type": self.tipo.pk, "data": {"finalidade": finalidade}},
            format="json",
        )


class StudentRequestTests(DocumentFlowBase):
    def test_anonimo_nao_acessa(self):
        self.assertEqual(self.client.get("/api/documentos/solicitacoes/").status_code, 401)

    def test_aluno_cria_solicitacao_com_protocolo_unico_e_historico(self):
        r1, r2 = self.criar(self.ana), self.criar(self.ana)
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r1.data["status"], "RECEIVED")
        self.assertNotEqual(r1.data["protocol"], r2.data["protocol"])
        self.assertEqual(len(r1.data["history"]), 1)

    def test_campo_obrigatorio_ausente_retorna_400(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.post(
            "/api/documentos/solicitacoes/",
            {"document_type": self.tipo.pk, "data": {}}, format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(DocumentRequest.objects.count(), 0)

    def test_tipo_inativo_nao_pode_ser_solicitado(self):
        self.tipo.active = False
        self.tipo.save()
        self.assertEqual(self.criar(self.ana).status_code, 400)

    def test_isolamento_entre_alunos(self):
        protocolo = self.criar(self.ana).data["protocol"]

        self.client.force_authenticate(self.bruno)
        self.assertEqual(self.client.get(f"/api/documentos/solicitacoes/{protocolo}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/documentos/solicitacoes/{protocolo}/arquivo/").status_code, 404)
        self.assertEqual(self.client.get("/api/documentos/solicitacoes/").data["count"], 0)

        self.client.force_authenticate(self.ana)
        self.assertEqual(self.client.get("/api/documentos/solicitacoes/").data["count"], 1)

    def test_aluno_nao_acessa_area_da_secretaria(self):
        self.client.force_authenticate(self.ana)
        self.assertEqual(self.client.get("/api/admin/solicitacoes/").status_code, 403)
        self.assertEqual(self.client.get("/api/admin/tipos-documento/").status_code, 403)

    def test_lista_de_tipos_somente_ativos(self):
        DocumentType.objects.create(name="Antigo", active=False)
        self.client.force_authenticate(self.ana)
        nomes = [t["name"] for t in self.client.get("/api/documentos/tipos/").data]
        self.assertEqual(nomes, ["Declaração de matrícula"])


class SecretaryFlowTests(DocumentFlowBase):
    def setUp(self):
        super().setUp()
        self.protocolo = self.criar(self.ana).data["protocol"]
        self.client.force_authenticate(self.secretaria)
        self.base = f"/api/admin/solicitacoes/{self.protocolo}"

    def estado(self, novo, note=""):
        return self.client.patch(f"{self.base}/estado/", {"status": novo, "note": note}, format="json")

    def test_secretaria_lista_e_filtra(self):
        self.criar(self.bruno)
        self.client.force_authenticate(self.secretaria)
        self.assertEqual(self.client.get("/api/admin/solicitacoes/").data["count"], 2)
        self.assertEqual(self.client.get("/api/admin/solicitacoes/?matricula=20260002").data["count"], 1)
        self.assertEqual(self.client.get("/api/admin/solicitacoes/?status=IN_REVIEW").data["count"], 0)

    def test_transicao_invalida_retorna_400(self):
        resp = self.estado("COMPLETED")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(DocumentRequest.objects.get(protocol=self.protocolo).status, "RECEIVED")

    def test_nao_conclui_sem_documento_final(self):
        self.assertEqual(self.estado("IN_REVIEW").status_code, 200)
        self.assertEqual(self.estado("COMPLETED").status_code, 400)

    def test_fluxo_completo_e_download_pelo_aluno(self):
        self.assertEqual(self.estado("IN_REVIEW", "Em conferência").status_code, 200)
        up = self.client.post(f"{self.base}/arquivo/", {"file": pdf()}, format="multipart")
        self.assertEqual(up.status_code, 201)
        self.assertTrue(up.data["has_file"])
        done = self.estado("COMPLETED")
        self.assertEqual(done.status_code, 200)
        self.assertEqual(done.data["allowed_transitions"], [])

        self.client.force_authenticate(self.ana)
        detalhe = self.client.get(f"/api/documentos/solicitacoes/{self.protocolo}/")
        self.assertEqual(detalhe.data["status"], "COMPLETED")
        self.assertTrue(detalhe.data["download_url"])
        baixar = self.client.get(f"/api/documentos/solicitacoes/{self.protocolo}/arquivo/")
        self.assertEqual(baixar.status_code, 200)
        self.assertEqual(b"".join(baixar.streaming_content), PDF_BYTES)
        self.assertEqual(baixar["Content-Type"], "application/pdf")

        self.client.force_authenticate(self.bruno)
        self.assertEqual(self.client.get(f"/api/documentos/solicitacoes/{self.protocolo}/arquivo/").status_code, 404)

    def test_download_sem_arquivo_retorna_404(self):
        self.client.force_authenticate(self.ana)
        self.assertEqual(self.client.get(f"/api/documentos/solicitacoes/{self.protocolo}/arquivo/").status_code, 404)

    def test_upload_invalido_e_rejeitado(self):
        falso = self.client.post(
            f"{self.base}/arquivo/", {"file": pdf("fake.pdf", b"nao sou pdf")}, format="multipart"
        )
        self.assertEqual(falso.status_code, 400)
        vazio = self.client.post(f"{self.base}/arquivo/", {"file": pdf("v.pdf", b"")}, format="multipart")
        self.assertEqual(vazio.status_code, 400)
        grande = self.client.post(
            f"{self.base}/arquivo/",
            {"file": pdf("g.pdf", b"%PDF-" + b"0" * (6 * 1024 * 1024))}, format="multipart",
        )
        self.assertEqual(grande.status_code, 400)

    def test_nao_anexa_em_solicitacao_indeferida(self):
        self.assertEqual(self.estado("REJECTED").status_code, 200)
        resp = self.client.post(f"{self.base}/arquivo/", {"file": pdf()}, format="multipart")
        self.assertEqual(resp.status_code, 400)

    def test_substituir_arquivo_remove_o_antigo(self):
        from django.db import transaction
        from .models import DocumentFile

        self.estado("IN_REVIEW")
        self.client.post(f"{self.base}/arquivo/", {"file": pdf()}, format="multipart")
        antigo = DocumentFile.objects.get().file.name
        storage = DocumentFile.objects.get().file.storage
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(f"{self.base}/arquivo/", {"file": pdf()}, format="multipart")
        novo = DocumentFile.objects.get().file.name
        self.assertNotEqual(antigo, novo)
        self.assertFalse(storage.exists(antigo))
        self.assertTrue(storage.exists(novo))

    def test_arquivo_fica_fora_de_url_publica(self):
        from django.conf import settings
        from .models import DocumentFile

        self.estado("IN_REVIEW")
        self.client.post(f"{self.base}/arquivo/", {"file": pdf()}, format="multipart")
        documento = DocumentFile.objects.get()
        self.assertTrue(documento.file.path.startswith(str(settings.PRIVATE_MEDIA_ROOT)))
        with self.assertRaises(ValueError):
            documento.file.url  # sem base_url: nunca há URL pública

    def test_acoes_administrativas_sao_auditadas_sem_segredos(self):
        self.estado("IN_REVIEW")
        self.client.post(f"{self.base}/arquivo/", {"file": pdf()}, format="multipart")
        acoes = set(AuditLog.objects.values_list("action", flat=True))
        self.assertEqual(acoes, {"REQUEST_STATUS_CHANGED", "REQUEST_FILE_ATTACHED"})
        self.assertTrue(all(a.actor == self.secretaria for a in AuditLog.objects.all()))

    def test_secretaria_gerencia_tipos_de_documento(self):
        resp = self.client.post(
            "/api/admin/tipos-documento/",
            {"name": "Histórico", "required_fields": ["finalidade"]}, format="json",
        )
        self.assertEqual(resp.status_code, 201)
        invalido = self.client.post(
            "/api/admin/tipos-documento/", {"name": "X", "required_fields": "texto"}, format="json"
        )
        self.assertEqual(invalido.status_code, 400)
        resp = self.client.patch(f"/api/admin/tipos-documento/{resp.data['id']}/", {"active": False}, format="json")
        self.assertFalse(resp.data["active"])
