# Relatório de qualidade — video_final.mp4

Gerado em 2026-11-06 15:53 por `lib/qc.py` (medições reais com ffprobe/ffmpeg).

**Resultado geral: APROVADO**

| Verificação | Resultado | Detalhe |
|---|---|---|
| Arquivo MP4 existe | OK | video_final.mp4 (32.3 MB) |
| Resolução 1080×1920 (9:16) | OK | 1080×1920 |
| FPS = 30 | OK | 30.000 fps, 1875 quadros |
| Codec de vídeo H.264 | OK | h264 / High / yuv420p |
| Áudio AAC presente | OK | aac 48000 Hz 2 canais |
| Duração entre 55 e 65 s | OK | 62.50 s |
| Áudio e vídeo com mesma duração | OK | vídeo 62.50 s / áudio 62.50 s |
| Sem quadros pretos indesejados | OK | pretos encontrados: 48.73–48.87s, 61.00–62.47s — todos intencionais (apagão / corte seco final) |
| Sem imagem congelada > 1,2 s (fora do final) | OK | nenhum congelamento |
| Loudness ≈ −14 LUFS | OK | -14.5 LUFS integrado |
| Sem clipping (pico < −0,5 dBFS) | OK | pico real -1.5 dBFS |
| Sem buracos de áudio (> 1,5 s abaixo de −55 dB) | OK | nenhum silêncio total |
| Todos os quadros renderizados | OK | 1875/1875 arquivos, 0 vazios |
| Prancha de amostragem gerada | OK | amostragem.png (1 quadro a cada 2 s) |

## Verificações visuais e de sincronismo (feitas abrindo as imagens)

- **Amostragem do vídeo final** (`storyboard/amostragem.png`, 1 quadro a cada 2 s): conferidos os 7 blocos da história. O gancho está no 1º segundo (o reflexo já se mexe com o protagonista imóvel), a troca dia→noite está em 24,2 s, o apagão no corredor, a revelação do quarto na janela e o corte seco para preto em 61,0 s.
- **Continuidade:** o copo âmbar, o vaso turquesa, a porta, a poltrona, o espelho com filete ciano e o figurino do personagem são os mesmos objetos 3D em todos os planos. Depois de cair, o copo fica no chão até a cena 3 (outro dia). A porta aberta na fuga é a mesma que o visitante usou.
- **Sincronismo:** os tempos de cada frase vêm da própria síntese da voz (`audio/voz/tempos.json`). Os efeitos usam os mesmos tempos das chaves de animação: queda do copo, batidas no vidro (8 impactos), piscar das luzes (mesma semente aleatória da cena) e lâmpadas apagando em 46,3 / 47,0 / 47,85 / 48,75 s.
- **Texto na tela:** o `projeto.blend` não tem nenhum objeto de texto (verificado: 313 malhas, 37 empties, 26 câmeras, 13 luzes, 5 armatures, 0 FONT). A montagem não adiciona legendas nem marca-d'água.
- **Trechos pretos intencionais:** em 48,73–48,87 s, o instante do apagão (0,14 s). De 61,0 s ao fim, o corte seco pedido no roteiro, com a batida suave no vidro sobre o preto.

## Limitações reais do ambiente (transparência)

1. **Resolução de render:** não há GPU, e o Eevee por software levou cerca de 90 s por quadro. Por isso os quadros foram renderizados em **540×960** (Cycles, 12 amostras + denoise, cerca de 8,7 s por quadro, 4,5 h no total) e **ampliados para 1080×1920** com Lanczos e nitidez leve. O arquivo final é 1080×1920 nativo em H.264, mas o detalhe fino equivale a uma renderização em meia resolução. Para render nativo em 1080×1920, rode `lib/render.py ... --pct 100` numa máquina com GPU.
2. **Voz:** é sintética (Kokoro TTS local, voz masculina pt-BR `pm_alex`), com pausas e ritmo ajustados frase a frase. Não é um locutor humano. Para trocar por uma gravação, substitua `audio/voz/voz.wav` mantendo os mesmos tempos e rode `lib/som.py` e `lib/montagem.py` de novo.
3. **Pesquisa de tendências:** os sites de vídeo não foram consultados nesta sessão, porque a rede do ambiente é restrita. O roteiro deste primeiro vídeo foi fornecido pelo usuário. Para os próximos, o skill `criar-video-3d` prevê a pesquisa quando houver acesso.
4. **Espelho:** o "reflexo do futuro" usa um mundo espelhado em 3D (escala −1), com o reflexo como segundo personagem animado independentemente. É o método pedido no briefing para tornar visível a defasagem temporal. Não há vídeo plano.

