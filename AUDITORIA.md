# AUDITORIA.md

# Auditoria técnica pré-produção (Fase 5)

Data: 2026-10-02. Escopo: itens do `MASTER-PROMPT.md` §21. Ambiente de verificação: PostgreSQL 16 local, API FastAPI, frontend Vite (build de produção) e Chromium (Playwright).

## Resumo

| Área | Situação | Evidência |
|---|---|---|
| Banco | OK | migrations `0001`–`0004` sobem/descem/sobem; modelos = migrations (teste automático); `CHECK` de subtotal, comprador único, tipos e valores positivos no próprio banco |
| API | OK | 200 testes de integração (todas as rotas: sucesso, 401, 404, 409, 422); OpenAPI gerado |
| Frontend | OK | 19 testes de componentes, 4 fluxos E2E no navegador, conferência visual por capturas de tela |
| Autenticação | OK | Argon2id; token vinculado a sessão revogável; expiração 8 h; limite de 5 falhas/15 min; mensagens genéricas |
| Autorização | OK | todas as rotas exceto login/health exigem ADMIN (teste varre o OpenAPI inteiro) |
| Filtros | OK | períodos fechados nas bordas; filtros de comprador/pagamento/recebimento só retornam vendas; ordenação com lista permitida |
| Datas | OK | "hoje" no fuso `America/Sao_Paulo` (teste 23h30 SP = 02h30 UTC); datas futuras recusadas |
| Valores monetários | OK | `Decimal`/`NUMERIC`, nunca `float`; JSON como string; entrada com > 2 casas recusada |
| Arredondamento | OK | `ROUND_HALF_UP` só no fim das divisões; casos 3,33 / 1,67 / 0,03; 1.000 vendas de R$ 0,01 = R$ 10,00 exato; teste de propriedade com 200 combinações |
| Concorrência | OK | versão otimista; teste com duas conexões reais: a primeira grava, a segunda recebe 409 sem sobrescrever |
| Auditoria | OK | toda criação/edição/ativação/exclusão/login gravada na mesma transação, com antes/depois; sem senhas/hash/tokens |
| Performance | OK | ~16 mil vendas (2 anos): todas as consultas do dashboard/histórico < 70 ms de mediana (meta 500 ms) |
| Dependências | OK | `npm audit`: 0 vulnerabilidades; `pip-audit`: 0 nas dependências da aplicação |
| Segredos no Git | OK | varredura de arquivos e histórico: nenhuma chave/token/senha real; apenas senhas fictícias de teste |
| Backup | OK | backup + restauração testados (banco novo e por cima de dados alterados): contagens e totais idênticos |
| Docker | **Pendente** | `docker compose config` válido; **build das imagens não executado** (ambiente sem daemon Docker) |

## Problemas encontrados e corrigidos nesta fase

| # | Problema | Correção |
|---|---|---|
| A-1 | Em produção, o sistema iniciaria com `JWT_SECRET` ou senha do banco de exemplo | Validação na inicialização: com `ENVIRONMENT=production` e valores de exemplo, a API **se recusa a iniciar** com mensagem clara (testes em `tests/unit/test_config.py`) |
| A-2 | Documentação técnica da API (`/api/docs`) exposta em produção | Desligada por padrão em produção (`ENABLE_API_DOCS` reativa) |
| A-3 | Vulnerabilidades conhecidas: React Router (moderada, vai ao navegador); Vite/Vitest (alta/crítica, ferramentas de desenvolvimento) | Atualizados para React Router 7.18, Vite 8, Vitest 5 → `npm audit`: 0. `pip`/`setuptools` atualizados na imagem do backend |
| A-4 | Série "vendas por empresa" percorria os dados uma vez por dia (141 ms em 366 dias) | Agregação em uma passada (66 ms) |
| A-5 | Backup não existia | Serviço `backup` diário com retenção de 30 dias, verificação do arquivo e scripts de backup/restauração (`ops/`) |
| A-6 | Logs sem limite de tamanho | Rotação no Docker (5 × 10 MB por serviço) |
| A-7 | Frontend iniciava antes de a API estar pronta | `depends_on: condition: service_healthy` |

## Riscos aceitos / pendências

| # | Item | Avaliação |
|---|---|---|
| R-1 | **Imagens Docker não construídas nesta sessão** | Validar no notebook servidor: `docker compose up -d --build`, `docker compose ps` (todos *healthy*) e `INSTALL.md` §7 |
| R-2 | Agendamento do backup usa `date -d` do contêiner Alpine (BusyBox), não testado aqui | Se não suportar, cai no plano B (a cada 24 h desde o início). Conferir `docker compose logs backup` na primeira semana |
| R-3 | HTTP sem TLS na rede local | Aceitável para uso em rede doméstica/empresarial privada com Wi-Fi protegido (WPA2/WPA3). Não expor a porta 8080 na internet |
| R-4 | Token de sessão em `sessionStorage` (exposto em caso de XSS) | Mitigado: CSP restritiva no Nginx, React escapa conteúdo, nenhum HTML de usuário é renderizado; sessão expira em 8 h e some ao fechar a aba |
| R-5 | Limite de tentativas de login é em memória (zera ao reiniciar a API) | Aceitável para 1–2 notebooks na rede local |
| R-6 | A tabela de auditoria é "somente inserção" na aplicação, mas o usuário do banco é dono das tabelas (pode alterá-las via SQL direto) | Aceitável para o porte; restringir permissões exigiria um usuário de banco separado para migrations. Registrado em `DATABASE.md` |
| R-7 | Consulta da auditoria só pela API (`/api/v1/audit-logs`), sem tela | Pode virar uma tela em versão futura |
| R-8 | Backups ficam no mesmo notebook | Cópia semanal externa é **obrigatória** (`OPERACAO.md` §2) |

## Como repetir a verificação

```bash
cd backend && pytest && ruff check . && mypy app && pip-audit
cd frontend && npm run test && npm run lint && npm run typecheck && npm run build && npm audit
cd frontend && npm run e2e        # com o sistema rodando
```
