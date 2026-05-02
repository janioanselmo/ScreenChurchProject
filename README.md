# ScreenChurchProject

## PT-BR

Aplicativo desktop em Python para projeção de imagens e vídeos em uma ou mais partes de uma saída de telão. O projeto foi pensado para operação em igrejas, cultos, eventos e ambientes com telão dividido em faixas ou áreas independentes.

## Visão Geral

O projeto usa **PyQt5** para criar uma janela de controle e uma janela de projeção no monitor/projetor escolhido. A projeção não fica mais limitada a três partes fixas: o operador pode iniciar com uma parte e adicionar novas partes com o botão `+ Parte`, respeitando a área máxima da saída selecionada.

Cada parte pode receber **imagem ou vídeo**. O software detecta o tipo de mídia importada e libera os controles adequados: imagens usam exibição estática/lista; vídeos liberam Play, Pause, Stop, avanço, retrocesso e barra de posição.

## Funcionalidades

- Interface desktop com PyQt5.
- Uma ou mais partes de projeção, criadas dinamicamente.
- Botão `+ Parte` para adicionar novas áreas de telão.
- Botão `- Parte` para remover a última área.
- Cada parte pode carregar imagem ou vídeo.
- Detecção automática do tipo de mídia.
- Controles de vídeo liberados somente quando a parte contém vídeo.
- Controles básicos de vídeo: Play, Pause, Stop, `-10s`, `+10s` e barra de progresso.
- Lista independente de mídias por parte.
- Histórico recente por parte.
- Pré-visualização antes de enviar a mídia para a parte.
- Tela preta rápida para ocultar a projeção.
- Loop de vídeo e avanço automático em listas de imagens.
- Seleção de monitor/projetor.
- Trava de dimensão: a soma das larguras das partes não pode ultrapassar a largura da saída selecionada.
- Trava de altura: nenhuma parte pode ultrapassar a altura da saída selecionada.
- Importação e exportação de configurações em JSON.
- Presets de layout de telão com quantidade de partes e dimensões.
- Importação/exportação JSON de sessão completa, incluindo listas e mídias recentes.
- Modo de operação para ocultar controles durante o uso.
- Atalhos de teclado para operação ao vivo.
- Build para Windows com PyInstaller.

## Fluxo de Uso

1. Selecione o monitor/projetor de saída.
2. Use `+ Parte` se precisar dividir o telão em mais áreas.
3. Clique em `Ajustes` para configurar largura e altura de cada parte.
4. O software valida se a soma das larguras cabe na saída selecionada.
5. Clique em `Selecionar mídia` em cada parte.
6. Use os controles adequados conforme a mídia:
   - imagem: exibição/lista/anterior/próxima;
   - vídeo: Play, Pause, Stop, avanço, retrocesso e barra de progresso.
7. Clique em `Projetar` para abrir a saída no monitor escolhido.


## Presets de Layout de Projeção

O software possui uma lista local de **layouts de projeção**. Esses layouts salvam apenas a estrutura do telão, sem depender das mídias carregadas.

Cada layout salva:

- nome do layout;
- resolução de referência da saída;
- quantidade de partes;
- largura e altura de cada parte.

Na barra superior existem os controles:

- `Layout`: lista de layouts disponíveis;
- `Aplicar layout`: aplica o layout selecionado;
- `Salvar layout`: salva o layout atual com um nome;
- `Excluir layout`: remove o layout selecionado.

Os layouts locais ficam no arquivo:

```text
projection_layout_presets.json
```

O programa cria automaticamente três layouts iniciais:

- `Full HD - 1 parte`: 1920 × 1080;
- `Full HD - 2 partes iguais`: 960 × 1080 + 960 × 1080;
- `Full HD - 3 partes iguais`: 640 × 1080 + 640 × 1080 + 640 × 1080.

Antes de aplicar um layout, o software valida a saída selecionada. A soma das larguras das partes não pode ultrapassar a largura da saída, e a altura máxima das partes não pode ultrapassar a altura da saída.

### Exemplo de arquivo `projection_layout_presets.json`

```json
{
  "schema_version": 2,
  "type": "screen_church_layout_presets",
  "presets": [
    {
      "name": "Full HD - 3 partes iguais",
      "output": {
        "width": 1920,
        "height": 1080
      },
      "panels": [
        {"width": 640, "height": 1080},
        {"width": 640, "height": 1080},
        {"width": 640, "height": 1080}
      ]
    }
  ]
}
```

## Exemplo de divisão Full HD

Para uma saída **1920 × 1080 px** dividida em três partes iguais:

| Parte | Largura | Altura |
| --- | ---: | ---: |
| Parte 1 | 640 px | 1080 px |
| Parte 2 | 640 px | 1080 px |
| Parte 3 | 640 px | 1080 px |

A soma das larguras é:

```text
640 + 640 + 640 = 1920 px
```

Portanto, a configuração é válida para uma saída 1920 × 1080.

## Estrutura

| Arquivo | Descrição |
| --- | --- |
| `screenChurch.py` | Ponto de entrada da aplicação |
| `app.py` | Bootstrap do `QApplication` |
| `main_window.py` | Janela principal, partes dinâmicas, controles, atalhos, monitores, listas, JSON e sessão |
| `media_widget.py` | Componente reutilizável para imagem e vídeo |
| `preview_dialog.py` | Pré-visualização antes de enviar a mídia |
| `projection_window.py` | Janela de projeção na saída selecionada |
| `projection_settings_dialog.py` | Configuração dinâmica das partes e validação contra a saída |
| `constants.py` | Constantes, extensões, textos, limites e versão do JSON |
| `build_windows.ps1` | Script base para gerar executável Windows com PyInstaller |
| `requirements.txt` | Dependências Python do projeto |
| `LICENSE` | Licença do repositório |
| `.gitignore` | Regras de arquivos ignorados pelo Git |

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Execução

```powershell
python screenChurch.py
```

## Gerar Executável Windows

```powershell
.\build_windows.ps1
```

## Formatos Suportados

### Imagens

- `.png`
- `.jpg`
- `.jpeg`
- `.bmp`
- `.gif`

### Vídeos

- `.mp4`
- `.avi`
- `.mov`
- `.wmv`
- `.mkv`
- `.flv`

### Observação sobre codecs

O componente de vídeo usa `QMediaPlayer` e `QVideoWidget`. O suporte real a vídeo depende dos codecs disponíveis no sistema operacional.

Formato recomendado para uso em igreja:

```text
MP4 com vídeo H.264 e áudio AAC
```

Outros formatos podem funcionar, mas dependem dos codecs instalados no Windows.

## Atalhos

- `F11`: iniciar/parar projeção.
- `Esc`: parar projeção.
- `B`: alternar tela preta.
- `Ctrl+,`: abrir ajustes de projeção.
- `Ctrl+1` até `Ctrl+9`: carregar mídia na parte correspondente.
- `Ctrl+Shift+1` até `Ctrl+Shift+9`: abrir mídia recente da parte correspondente.
- `Alt+1` até `Alt+9`: limpar a parte correspondente.

## Importação e Exportação JSON

Os presets são exportados como JSON com extensão sugerida:

```text
.scpreset.json
```

O JSON salva:

- versão do esquema;
- monitor selecionado;
- resolução da saída detectada;
- estado de projeção;
- loop;
- blackout;
- quantidade de partes;
- dimensões de cada parte;
- caminho da mídia atual;
- tipo de mídia detectado;
- lista de mídias de cada parte;
- posição atual da lista;
- histórico recente.

### Exemplo de preset JSON

```json
{
  "schema_version": 2,
  "screen_index": 1,
  "output": {
    "width": 1920,
    "height": 1080
  },
  "fullscreen": false,
  "operation_mode": false,
  "blackout": false,
  "loop": true,
  "panel_count": 3,
  "panels": [
    {
      "index": 1,
      "path": "C:/midias/lateral-esquerda.mp4",
      "media_type": "video",
      "width": 640,
      "height": 1080,
      "playlist": [],
      "playlist_position": 0,
      "recent_media": []
    },
    {
      "index": 2,
      "path": "C:/midias/centro.png",
      "media_type": "image",
      "width": 640,
      "height": 1080,
      "playlist": [],
      "playlist_position": 0,
      "recent_media": []
    },
    {
      "index": 3,
      "path": "C:/midias/lateral-direita.mp4",
      "media_type": "video",
      "width": 640,
      "height": 1080,
      "playlist": [],
      "playlist_position": 0,
      "recent_media": []
    }
  ]
}
```

## Notas Técnicas

- O projeto depende de `PyQt5>=5.15,<5.16`.
- O empacotamento para Windows usa `PyInstaller`.
- A reprodução de vídeo usa `QMediaPlayer` e `QVideoWidget`.
- A janela de projeção abre sem bordas no canto superior esquerdo da tela selecionada.
- A largura total da projeção é a soma das larguras das partes.
- A altura total da projeção é a maior altura configurada entre as partes.
- A configuração só é aplicada/projetada quando respeita a resolução da saída selecionada.

## Licença

Consulte `LICENSE`.

---

## English

Desktop Python application for projecting images and videos into one or more parts of a screen output. It is designed for churches, services, events, and projection systems where the output may be divided into independent areas.

## Overview

The project uses **PyQt5** to create a control window and a projection window on the selected monitor/projector. Projection is no longer limited to three fixed panels: the operator can start with one part and add more using the `+ Parte` button, while respecting the selected output resolution.

Each part can display either an **image or a video**. The software detects the imported media type and enables the proper controls. Image panels use static display/list navigation; video panels enable Play, Pause, Stop, seek backward, seek forward, and the progress bar.

## Features

- PyQt5 desktop interface.
- Dynamic projection parts.
- `+ Parte` button to add new projection areas.
- `- Parte` button to remove the last area.
- Each part can load an image or video.
- Automatic media type detection.
- Video controls enabled only for video media.
- Basic video controls: Play, Pause, Stop, `-10s`, `+10s`, and progress bar.
- Independent media list per part.
- Recent media history per part.
- Preview before sending media to a part.
- Quick blackout.
- Video loop and automatic image-list advance.
- Monitor/projector selection.
- Dimension lock: the sum of part widths cannot exceed the selected output width.
- Height lock: no part height can exceed the selected output height.
- JSON import/export for projection presets.
- Operation mode to hide controls during live use.
- Keyboard shortcuts for live operation.

## Recommended Video Format

```text
MP4 with H.264 video and AAC audio
```

Other formats may work depending on the codecs installed on the operating system.

## JSON Import and Export

Preset files use the suggested extension:

```text
.scpreset.json
```

They store the schema version, selected output, panel count, panel dimensions, current media paths, detected media type, playlists, and recent media history.

## Run

```powershell
python screenChurch.py
```

## License

See `LICENSE`.


## Observação importante sobre reprodução de vídeo

O ScreenChurchProject usa `QMediaPlayer` do PyQt5. No Windows, esse recurso
depende dos codecs instalados no sistema e dos plugins de multimídia do Qt
incluídos no executável.

Formato recomendado para maior compatibilidade:

```text
MP4 com vídeo H.264 e áudio AAC
```

Formatos como AVI, MOV, WMV, MKV e FLV podem funcionar, mas dependem dos
codecs disponíveis no computador. Se um vídeo não abrir, converta para MP4
H.264/AAC.

Para gerar o executável, use o `build_windows.ps1` atualizado, pois ele chama o
`ScreenChurchProject.spec` com coleta explícita dos componentes de multimídia
do PyQt5.


## Reprodução de vídeos: backend VLC recomendado

A partir desta versão, o ScreenChurch tenta usar o **VLC** como backend principal de vídeo quando ele está disponível. Isso aumenta muito a compatibilidade com formatos como:

- `.mp4`
- `.mov`
- `.mkv`
- `.avi`
- `.wmv`
- `.flv`

### Instalação recomendada no Windows

1. Instale o **VLC Media Player 64-bit** no Windows.
2. Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

O pacote `python-vlc` já está incluído no `requirements.txt`. Ele permite que o Python controle o VLC dentro da janela do ScreenChurch.

Se o VLC não estiver instalado, o software volta automaticamente para o backend `Qt Multimedia`, mas esse backend depende dos codecs do Windows e pode falhar mesmo com arquivos `.mp4`. Por isso, para uso em igreja, recomenda-se fortemente instalar o VLC 64-bit.

### Formato mais seguro

Mesmo com VLC, o formato mais recomendado continua sendo:

```text
MP4 com vídeo H.264 e áudio AAC
```

### Como identificar o backend usado

No rodapé do painel, o software mostra:

```text
VLC
```

ou

```text
QT
```

Quando aparecer `VLC`, a reprodução está usando o backend mais compatível.
