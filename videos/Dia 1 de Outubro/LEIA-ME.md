# Dia 1 de Outubro — edição

Origem: `Marca Pessoal Dia 1 de Outubro Pré Claude.mp4` (4K vertical, H.264 8-bit, 60 fps, 49,5 s, já pré-cortado por ti).
Resultado: **44,7 s** a 1.1x (tom de voz preservado), voz a **-14 LUFS**. **A cor não foi mexida.**

## Estado
- [x] **Pré-visualização 1080p** para aprovação — `Dia 1 de Outubro - PREVIEW 1080p.mp4`
- [ ] Final 4K (plate 10-bit sem texto + texto ProRes 4444 com alpha + áudio separado + versão completa) — só depois de aprovares

## Corte
O vídeo já vinha cortado frase a frase (16 jump cuts, sem frases repetidas nem hesitações), por isso só apertei
as 4 pausas que passavam de 0,19 s nos cortes existentes (−0,37 s no total) e passei a 1.1x. A nova transcrição
do resultado confirma todas as frases, pela ordem, sem palavras cortadas.
No fim não há gesto de mão à câmara, por isso o vídeo termina em "dezembro" (com um fade de 30 ms no áudio, porque o original corta seco).

## Motion graphics (diferentes do "Dizer não a clientes")
| Momento | Recurso |
|---|---|
| Hook "faltam 92 dias" | **"92" gigante atrás da cabeça** (recorte da silhueta: cabeça e mão ficam à frente), entra arrastado com rasto e os números a rolar de 365 até 92, impacto + abanão de câmara ao aterrar |
| "…a minha maior desculpa" | "desculpa" em itálico serifado riscada a marcador âmbar |
| "Tenho trabalhos para marcas… vídeos pessoais" | **Lista numerada ao peito** (01–04) que cresce com cada "tenho"; em "alguma coisa tem de ficar de fora" o resto apaga-se e "vídeos pessoais" é riscado; em "é sempre isto" fica só esse |
| "não era falta de tempo / era falta de prazo" | "tempo" riscado, "prazo" em âmbar com círculo desenhado à mão + punch-in |
| "o primeiro a cair" | a palavra "cair" cai |
| "vou publicar todos os dias até 31 de dezembro" | **Ecrã editorial de calendário** (papel quadriculado creme): grelha dos 92 dias out→dez, dia 1 preenchido e circulado ("hoje"), os 92 dias enchem-se em âmbar, 31 dez circulado, tira de papel "92 dias · 92 vídeos" |
| CTA "Comenta já foste" | **Caixa de comentário do Instagram** a escrever "já foste" letra a letra |

O espaço de cima só é usado no hook. Zooms (poucos, centrados na cara) só em cima de jump cuts já existentes:
hook, "é sempre isto", "falta de prazo", "então, a partir de hoje", e um push-in lento no CTA.
Todas as frames verificadas dentro das margens seguras Reels/TikTok (letras reais, não caixas).

> Ideia para a série: o calendário dos 92 dias pode voltar em todos os vídeos com mais um dia preenchido.

## Pipeline
`edit-pipeline/dia1-outubro/` — `edl.py` (corte), `audio.py` (voz 1.1x, -14 LUFS), `sfx.py` (efeitos), `render/` (legendas e gráficos em HTML → PNG com alpha), `comp.py` (composição 16-bit, recorte de profundidade, preview/final), `safe_check.py` (margens frame a frame).
