---
name: criar-video-3d
description: >
  Use quando o usuário pedir "Crie outro vídeo", "faça um novo short", "novo vídeo What If", ou qualquer novo
  vídeo vertical 3D do estúdio (Shorts/Reels/TikTok, 9:16, ~60 s, narração em PT-BR, sem texto na tela) feito
  em Blender por código. Cobre: checar o histórico de ideias, criar premissa original, roteiro, cena Blender
  (personagem grafite com armature), narração TTS, trilha/efeitos sintetizados, render, montagem, QC e entrega.
---

# Estúdio de Shorts 3D originais (Blender + Python)

Tudo vive em `estudio/` na raiz do repositório:

| Caminho | O que é |
|---|---|
| `estudio/historico_ideias.json` | histórico persistente + conceitos bloqueados. **Ler antes de qualquer ideia nova.** |
| `estudio/lib/bu.py` | utilitários bpy: materiais, primitivas, luzes, câmeras, keyframes (`F(t)` = segundo→frame) |
| `estudio/lib/personagem.py` | personagem humanoide grafite com armature + `Actor` (poses, `locomote` = andar/correr) |
| `estudio/lib/tts.py` | narração PT-BR (Kokoro, voz masculina `pm_alex`), gera `voz.wav` + `tempos.json` por frase |
| `estudio/lib/som.py` + `lib/audio_kit/` | efeitos originais sintetizados, trilha por humor, ambiências, ducking |
| `estudio/lib/render.py` | `stills`, `shots` (1 still por plano) e `anim` (frames) a partir do `.blend` |
| `estudio/lib/montagem.py` | frames + mix → MP4 H.264/AAC 1080×1920 30 fps, −14 LUFS |
| `estudio/lib/qc.py` | verificação real (ffprobe/ffmpeg) → `relatorio_qualidade.md` + prancha |
| `estudio/videos/001_reflexo_futuro/` | **projeto de referência completo** (copiar a estrutura) |

## Regras de conteúdo (do usuário)
- Proibido QUALQUER texto, legenda, título, número, gráfico ou marca-d'água na imagem. Nunca criar objetos de texto.
- Narração PT-BR masculina, curiosa no início, tensão crescente, pausas estratégicas (números nas `parts` = pausa).
- Pergunta-gancho no início; o 1º segundo já mostra algo visualmente surpreendente.
- Acontecimentos cada vez mais surpreendentes; final impactante/inesperado/emocional; história completa.
- Personagem: humanoide grafite, cabeça redonda, dois olhos claros, articulado; deve andar, correr, virar a
  cabeça, manipular objetos, reagir (nada de "deslizar").
- Não copiar roteiros, personagens ou conceitos do Ifverse; respeitar `conceitos_bloqueados`.
- 55–65 s, 1080×1920, 30 fps, MP4 H.264 + AAC.

## "Crie outro vídeo" — passo a passo
1. **Histórico:** ler `estudio/historico_ideias.json`. Listar fenômenos, conflitos, reviravoltas e finais já usados.
2. **Pesquisa (se houver internet):** procurar tendências recentes de What If / sci-fi / hipotéticos. Usar como
   inspiração de princípios (gancho, escalada, final), nunca copiar. Não alegar ineditismo mundial.
3. **Premissa nova:** rejeitar se o fenômeno, o conflito ou o final forem iguais ou parecidos com algum do
   histórico (trocar personagem/cenário/número NÃO conta como novo). Priorizar ideias filmáveis em interiores/
   exteriores simples e com uma "imagem impossível" forte. Registrar no histórico com `"estado": "em_producao"`.
4. **Roteiro:** 6–8 cenas, ~60 s, falas curtas. Criar `videos/NNN_slug/scripts/narracao.json` (ver o 001) e rodar
   `python3 -I estudio/lib/tts.py <narracao.json> <video>/audio/voz` → ajustar `start` de cada linha até caber.
   Os tempos por frase em `audio/voz/tempos.json` guiam a sincronização de gestos e cortes.
5. **Cena Blender:** copiar `videos/001_reflexo_futuro/scripts/cena.py` como base e reescrever cenário, ações e
   câmeras. Padrões que funcionaram:
   - `shot(id, t0, t1, pos0, pos1, alvo0, alvo1, lens, fstop)` cria câmera animada + marcador de timeline.
   - Cortes com teleporte: `cut_place` / `cut_pose`. Objetos na mão: `hand_hold` (Child Of animado).
   - Eixos do rig (verificados): cabeça Y negativo = vira para a direita do personagem; braço X negativo = para
     frente; joelho X positivo = dobra. Personagem com yaw 180 olha para +Y.
   - "Mundo do espelho" = coleção instanciada sob um empty com escala Y −1 (truque de cinema, permite o reflexo
     agir sozinho). Coleções instanciadas também servem para cenários-fantasma.
   - Luzes de área nunca visíveis à câmera (`visible_camera=False`); dia/noite por keyframes de energia.
   - Uma cor de destaque por objeto-chave da história; personagem sempre grafite; rim/brilho frio em momentos-chave.
   Rodar `python3 -I scripts/cena.py projeto.blend` dentro da pasta do vídeo.
6. **Storyboard/QC visual antes do render:** `python3 -I ../../lib/render.py projeto.blend shots renders/sheet --pct 25 --samples 8 --at 0.2,0.8`
   e montar prancha com ffmpeg `tile`. **Abrir as imagens e corrigir** enquadramento, direção do olhar, objetos
   fora do lugar, cenas escuras demais. Para dúvidas de direção, medir numericamente (posição dos olhos) em vez de adivinhar.
7. **Som:** escrever `scripts/som_cues.py` (ver o 001: trilha por humor, ambiências, efeitos com tempos absolutos,
   `mirror: true` = som abafado, `cut` = corte seco) → `python3 -I ../../lib/som.py audio/cues.json audio/voz/voz.wav audio`.
8. **Render final:** Cycles CPU (12 amostras + OpenImageDenoise, dados persistentes) em 540×960 (`--pct 50`),
   ampliado na montagem. Nesta máquina (4 CPUs, sem GPU) ≈ 9 s/quadro ≈ 4,5 h para 60 s. Rodar destacado:
   `setsid nohup python3 -I ../../lib/render.py projeto.blend anim <frames> --from 0 --to <dur> --pct 50 > log 2>&1 &`
   (retomável: quadros prontos são pulados; apagar arquivos de 0 byte antes de retomar). Eevee aqui só roda por
   software (llvmpipe) e é ~10× mais lento — não usar sem GPU.
9. **Montagem:** `python3 -I ../../lib/montagem.py <frames> audio/mix.wav video_final.mp4`.
10. **QC:** `python3 -I ../../lib/qc.py video_final.mp4 relatorio_qualidade.md storyboard/amostragem.png --expect-black <t> --frames_dir <frames> --nframes <n>`;
    abrir a prancha e conferir. Só dizer que está pronto depois do QC.
11. **Entrega:** pasta do vídeo com `video_final.mp4`, `projeto.blend`, `scripts/`, `audio/`, `renders/`,
    `storyboard/`, `historico_ideias.json` (cópia), `relatorio_qualidade.md`. Atualizar o histórico para
    `"produzido"`. Frames brutos ficam em `_deps/` (ignorado pelo git). Commitar e enviar no branch de trabalho.

## Dependências (instalar se a sessão for nova)
```bash
pip install bpy scipy kokoro-onnx soundfile          # Blender 5.x como módulo Python + áudio + TTS
mkdir -p _deps/kokoro && cd _deps/kokoro && \
  curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx && \
  curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```
ffmpeg precisa estar no sistema. Limitação conhecida: a voz Kokoro `pm_alex` é natural para TTS local, mas não
iguala um locutor humano; o pipeline aceita trocar `audio/voz/voz.wav` por uma gravação externa (manter os tempos).
