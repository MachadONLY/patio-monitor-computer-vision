# Demonstração pública do Pátio Monitor

Esta configuração reúne o frontend, o FastAPI, a gravação anotada e o Qwen local em um único serviço. O modo LIVE consulta o feed público do BRT do Rio de Janeiro. A cena DEMO usa dados sintéticos e os identifica na interface.

## Render

1. Abra o [Blueprint da demonstração](https://render.com/deploy?repo=https://github.com/MachadONLY/patio-monitor-computer-vision/tree/deploy-publico) e entre na sua conta do Render.
2. Revise o plano de 2 GB indicado no Blueprint e confirme a criação se estiver de acordo com o preço exibido.
3. Aguarde o build e abra a URL pública exibida no painel. O primeiro build baixa o peso GGUF e verifica o SHA-256 do manifesto.

A aplicação usa a URL HTTPS definida pelo Render para validar a origem do WebSocket. O serviço publica apenas a demonstração. O GPS da SPTrans e o replay assinado dependem dos dados e credenciais da operação.

## Conferência após a publicação

- Abra a URL pública e confira o pátio no modo DEMO.
- Abra **Câmera do portão**, reproduza a gravação e selecione o cruzamento de 7,44 s.
- Em **Revisar turno**, selecione uma ocorrência de troca de veículo e use **Explicar ocorrência**. Confira a fonte retornada.
- Selecione **LIVE** e confira a origem do BRT do Rio e o horário dos registros, quando disponíveis.
