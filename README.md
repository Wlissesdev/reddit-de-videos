# Reddit DE Videos

Automação **100% gratuita** para gerar vídeos estilo Reddit Story em alemão.

## O que faz

Para cada história no JSON, o script gera automaticamente:

1. **Balão Reddit** (estilo Postfully) com título, subreddit e username
2. **Narração em alemão** do título e da história (Google TTS — grátis)
3. **Legendas sincronizadas** palavra a palavra
4. **Vídeo final** vertical (1080×1920) pronto para TikTok/Reels/Shorts

## Estrutura do vídeo

```
[0s ───────────── título ─────────────]  Balão Reddit visível + narrador lê o título
[título ──────────────────── fim]        Balão some + legendas + narrador conta a história
```

## Requisitos (grátis)

- Python 3.10+
- FFmpeg no PATH
- Internet (para gerar áudio via Google TTS)

## Instalação

```powershell
cd C:\Users\wliss\Projects\reddit-de-videos
pip install -r requirements.txt
```

## Uso

1. Coloque seu vídeo de fazenda em `input/video.mp4`
2. Copie e edite as histórias:

```powershell
copy input\stories.example.json input\stories.json
```

3. Gere todos os vídeos:

```powershell
python src\main.py
```

4. Vídeos prontos em `output/video_01.mp4`, `video_02.mp4`, etc.

### Gerar só alguns vídeos

```powershell
python src\main.py --from 1 --to 5
```

## Formato do JSON

```json
[
  {
    "title": "Título da história em alemão",
    "body": "Texto completo da história...",
    "subreddit": "r/lustig",
    "username": "u/Anonym"
  }
]
```

## Configuração (`config.yaml`)

- `voice`: voz alemã (`de-DE-ConradNeural`, `de-DE-KatjaNeural`, etc.)
- `width` / `height`: resolução de saída
- `bubble`: tempo extra do balão, fade out, upvotes fake
- `subtitles`: tamanho e posição das legendas

## Stack gratuita

| Etapa | Ferramenta | Custo |
|-------|-----------|-------|
| Narração | [gTTS](https://github.com/pndurette/gTTS) | R$ 0 |
| Balão Reddit | Pillow (desenho local) | R$ 0 |
| Legendas | Geradas do timing do TTS | R$ 0 |
| Edição | FFmpeg | R$ 0 |

## Dicas

- **30 histórias**: coloque todas no `stories.json` e rode uma vez — sai 30 vídeos
- **Mesmo vídeo de fundo**: o script faz loop automático se o áudio for mais longo
- **Voz melhor (opcional)**: com Python 3.12 você pode trocar gTTS por Edge TTS (voz neural Microsoft, também grátis)
- **Postfully manual**: não precisa — o balão é gerado automaticamente no estilo Reddit

## Próximos passos opcionais

- Agendar upload automático (TikTok/YouTube API)
- Música de fundo royalty-free
- Thumbnail automática
- Traduzir histórias do Reddit EN → DE com modelo local
