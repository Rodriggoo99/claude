# Dizer não a clientes — edição (versão final v4)

Origem: `dji_mimo_20260927_172326…MP4` (4K 10-bit HEVC, 4 min). Resultado: **29,06 s** a 1.1x, 4K vertical (2160×3840) 59.94fps.
**A cor não foi mexida** — a imagem está no perfil original da DJI, pronta para graduares.

## Ficheiros para o CapCut

| Ficheiro | Para quê |
|---|---|
| `plate_10bit_sem_texto.mp4` | **Faixa 1 — para graduar:** corte + velocidade + zooms + abanões + desfoque da citação, sem texto, HEVC 10-bit alta qualidade |
| `texto_legendas_CapCut_ProRes4444.mov` | **Faixa 2 — por cima, sem cor:** legendas + gráficos com transparência (ProRes 4444 com alpha). Já tem a profundidade recortada (NÃO / chega. / "não" atrás de ti), o ecrã de papel e o véu escuro da citação |
| `audio_final_mix.wav` | Voz + efeitos, -14 LUFS |
| `audio_voz.wav` / `audio_efeitos.wav` | Stems separados, se quiseres ajustar volumes |
| `Dizer Nao a Clientes - Final (sem cor) H264.mp4` / `… 10bit HEVC.mp4` | Versão completa (referência) |
| `Dizer Nao a Clientes - v3/v4 PREVIEW 1080p.mp4` | Pré-visualizações de aprovação |

## Montagem no CapCut
1. Projeto 2160×3840 (9:16, 4K) a 59.94fps.
2. `plate_10bit_sem_texto.mp4` na faixa principal → aplica a cor.
3. `texto_legendas_CapCut_ProRes4444.mov` como sobreposição, escala 100%, posição centro, **sem** cor.
4. `audio_final_mix.wav` no áudio (e tira o som do plate). Tudo começa em 00:00 e alinha frame a frame.

## O que tem a v4
- Hook: NÃO gigante arrastado com whoosh + impacto + abanão, atrás da cabeça.
- Legendas ao peito (1–3 palavras, etiqueta Inter Bold + Inter Tight / Instrument Serif, destaque âmbar #F2B24C).
- Ecrã editorial (papel quadriculado creme, tiras rasgadas, gráfico à mão: mais clientes ↑ / menos faturação ↓).
- "chega." atrás da cabeça; 4 "não" espalhados atrás de ti.
- Citação sobre o teu próprio plano desfocado e escurecido, círculo âmbar à mão em "melhor".
- Final: a mão vai até à lente (CTA visual) e o vídeo termina quando a tapa.
- Margens seguras Reels/TikTok verificadas frame a frame (só a entrada arrastada do NÃO e a saída do papel passam a margem, de propósito, em movimento).

Pipeline: `edit-pipeline/dizer-nao/` (`run_final.sh`).
