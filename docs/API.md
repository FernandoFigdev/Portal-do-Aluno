# API do Portal Unificado do Aluno

Base: `http://127.0.0.1:8000/api/` · Formato: JSON · Autenticação: `Authorization: Bearer <access>`.
Listas são paginadas: `{"count", "next", "previous", "results"}` (20 por página, `?page=2`).

## Erros
| HTTP | Quando | Corpo |
|---|---|---|
| 400 | Validação | `{"campo": ["mensagem"]}` ou `{"status": "mensagem"}` |
| 401 | Sem token/expirado | `{"detail": "..."}` |
| 403 | Perfil sem permissão | `{"detail": "..."}` |
| 404 | Não existe **ou pertence a outro aluno** | `{"detail": "..."}` |
| 409 | Aluno sem vínculo no sistema externo | `{"code": "student_not_linked", "detail": "..."}` |
| 429 | Muitas tentativas de login | `{"detail": "..."}` |
| 503 | Sistema externo indisponível | `{"code": "integration_unavailable", "detail": "..."}` |

## Autenticação (RF01, RF02)
| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| POST | `/auth/login/` | `{"username","password"}` (username = matrícula) | `{"access","refresh"}` |
| POST | `/auth/refresh/` | `{"refresh"}` | novo `access` (e novo `refresh`) |
| POST | `/auth/logout/` | `{"refresh"}` | invalida o refresh |
| GET | `/me/` | – | `{id, username, first_name, last_name, email, role, student}` |

`role`: `STUDENT`, `STAFF` (secretaria) ou `ADMIN`. O access dura 15 min; o refresh, 1 dia.

## Painel e integrações
| Método | Rota | Perfil | Observação |
|---|---|---|---|
| GET | `/dashboard/` | Autenticado | Contagens por estado, certificados e atalhos |
| GET | `/integracoes/status/` | Autenticado | Por serviço: `configured` e `last_check` |
| GET | `/integracoes/atalhos/` | Autenticado | `[{key, name, url}]` (Cerbrum / SECTRAS) |

## Acadêmico (RF05–RF08) — perfil Aluno
`GET /academico/disciplinas/`, `/academico/notas/`, `/academico/materiais/`

```json
{"source": "SECTRAS Online", "fetched_at": "2026-11-09T19:00:00-03:00",
 "results": [{"code": "POO", "name": "Programação Orientada a Objetos"}]}
```
Notas: `{course_code, course_name, period, value}` · Materiais: `{course_code, title, url}`.
Se a fonte falhar: **503** sem `results` (nunca dados simulados). Hoje o Cerbrum retorna 503 (sem API confirmada).

## Documentos — Aluno (RF13–RF16, RF19)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/documentos/tipos/` | Tipos ativos: `{id, name, description, required_fields}` |
| POST | `/documentos/solicitacoes/` | `{"document_type": 1, "data": {"finalidade": "Estágio"}}` → **201** com `protocol` |
| GET | `/documentos/solicitacoes/` | Somente as do aluno logado |
| GET | `/documentos/solicitacoes/{protocolo}/` | Detalhe + `history` |
| GET | `/documentos/solicitacoes/{protocolo}/arquivo/` | Download do PDF (404 se ainda não disponível) |

`status`: `RECEIVED`, `IN_REVIEW`, `AWAITING_INFO`, `COMPLETED`, `REJECTED` (`status_display` traz o rótulo em português).

## Documentos — Secretaria (RF17, RF18)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/admin/solicitacoes/` | Filtros: `?status=`, `?protocolo=`, `?matricula=`, `?tipo=<id>` |
| GET | `/admin/solicitacoes/{protocolo}/` | Inclui `student`, `allowed_transitions`, histórico com `changed_by` |
| PATCH | `/admin/solicitacoes/{protocolo}/estado/` | `{"status": "IN_REVIEW", "note": "opcional"}` |
| POST | `/admin/solicitacoes/{protocolo}/arquivo/` | `multipart/form-data`, campo `file` (PDF) |
| GET | `/admin/solicitacoes/{protocolo}/arquivo/` | Baixa o PDF anexado |
| GET/POST/PATCH | `/admin/tipos-documento/` | Cadastro dos tipos (`name`, `description`, `required_fields`, `active`) |

Transições: `RECEIVED → IN_REVIEW | REJECTED`; `IN_REVIEW → AWAITING_INFO | COMPLETED | REJECTED`;
`AWAITING_INFO → IN_REVIEW | REJECTED`. Para `COMPLETED` o PDF final precisa estar anexado.

## Certificados
**Aluno (RF21, RF23):** `GET /certificados/`, `GET /certificados/{id}/`, `GET /certificados/{id}/download/`.

**Secretaria (RF22, RF24):**
| Método | Rota | Descrição |
|---|---|---|
| POST | `/admin/certificados/` | `multipart`: `student` (**matrícula**), `category`, `title`, `description?`, `file` (PDF/PNG/JPG) |
| GET | `/admin/certificados/` | Filtros: `?matricula=`, `?categoria=` |
| GET | `/admin/certificados/{id}/` · `/download/` | Detalhe e download |
| PATCH | `/admin/certificados/{id}/` | Corrige campos, reassocia `student` ou troca `file` |

## Auditoria (RF25) — somente `ADMIN`
`GET /admin/auditoria/` com filtros `?acao=`, `?tipo=`, `?alvo=`. Ações: `REQUEST_STATUS_CHANGED`,
`REQUEST_FILE_ATTACHED`, `CERTIFICATE_CREATED`, `CERTIFICATE_UPDATED`.

## Exemplo de uso no front (fetch)
```js
const r = await fetch("http://127.0.0.1:8000/api/auth/login/", {
  method: "POST", headers: {"Content-Type": "application/json"},
  body: JSON.stringify({username: "20260001", password: "..."}),
});
const {access} = await r.json();
const me = await fetch("http://127.0.0.1:8000/api/me/", {headers: {Authorization: `Bearer ${access}`}});
```
Defina `CORS_ALLOWED_ORIGINS` no `.env` com a origem do front (ex.: `http://localhost:5173`).
