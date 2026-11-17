# Deploy público — Pátio Monitor

Esta configuração publica a **mesma aplicação avaliada**: React/Three.js, API FastAPI, Qwen local, gravação real anotada e feed GPS público MOBI-Rio. Não usa o serviço do Felipe.

## Plataforma recomendada

Use Railway com um serviço **Docker** conectado ao repositório
`MachadONLY/patio-monitor-computer-vision`, branch `main`.
O Dockerfile na raiz é detectado automaticamente. A aplicação é executada como usuário sem privilégios, com apenas um worker e o modelo Qwen quantizado no próprio contêiner.

**Recurso necessário:** permita pelo menos **2 GB RAM** para a API, modelo e interface. Não use o plano Free/Trial com 0,5–1 GB como se isso garantisse o funcionamento. Railway Hobby tem cobrança mínima e uso variável; confirme preços e limites antes de habilitar uma assinatura. Não configure pagamentos sem autorização do responsável pela conta.

## Configuração

1. Conecte a sua conta Railway ao GitHub correto (`MachadONLY`).
2. Crie um projeto e selecione **Deploy from GitHub Repo**, escolhendo `MachadONLY/patio-monitor-computer-vision`. Mantenha a raiz `/`.
3. Confira os logs: o Dockerfile precisa executar `pnpm build`, instalar o runtime CPU e baixar o GGUF oficial, validando seu SHA-256.
4. Configure `PATIO_LIVE_PROVIDER=rio_brt` (já é padrão) e volume persistente montado em `/srv/patio/data` se precisar guardar GPS durante toda a avaliação.
5. Na seção de serviço **Settings → Networking → Public Networking**, clique em **Generate Domain**. O serviço recebe `RAILWAY_PUBLIC_DOMAIN` automaticamente; o startup ajusta `PATIO_PUBLIC_ORIGIN` para esse HTTPS.
6. Configure **Healthcheck Path: /health** e ative reinício automático do serviço caso ocorra falha.
7. Abra a URL gerada numa janela anônima. Verifique o tour, a resposta do Qwen e a reprodução em 7,44s. O GPS público pode ficar indisponível em alguns horários sem que posições sejam inventadas.

## Segredos de RPA

A integração opcional do Smart Bus Gate utiliza `RPA_API_URL` e `RPA_API_KEY`. Defina ambos em **Variables** no painel Railway, nunca no README/GitHub. A chave de consulta deve permanecer apenas no servidor. O painel de cancela comunica claramente quando o provedor externo está indisponível.

## Critérios de aceite público

- `GET /health` retorna `{"status":"ok"}`
- `GET /` retorna a interface 3D, com botão **Iniciar teste guiado**
- `GET /api/gs/vision` contém um cruzamento e `/api/gs/vision/media/annotated.mp4` serve o MP4
- `POST /api/gs/explain` retorna orientação gerada pelo Qwen local e pelo menos a fonte p02 para o caso PM-0615
- `GET /api/vehicles/snapshot?mode=LIVE` identifica `rio_mobi_gtfs_rt`; a ausência de veículos deve ser comunicada sem apresentar dados simulados como atuais
- Abrir numa janela anônima funciona sem login

A URL deve continuar acessível **durante a correção**. Não use Codespaces, que para por inatividade, como hospedagem definitiva. Nenhuma configuração de hospedagem garante disponibilidade de terceiros (feed GPS, n8n) ou uso comercial validado sem testes operacionais em campo.
