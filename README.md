# ScreenChurch Project

Software de projeção para igrejas feito em **Python + PyQt5 + VLC**, com layouts dinâmicos, partes configuráveis, mídia por parte, letras, Bíblia importável por JSON, temas e fluxo seguro **Prévia → Ao vivo**.

---

## PT-BR

### 1. Arquitetura de armazenamento

A partir desta versão, os dados do ScreenChurch ficam separados do código do programa em uma pasta local chamada **ScreenChurchData**.

Nesta entrega, o ZIP já vem com uma pasta **ScreenChurchData/** ao lado dos arquivos `.py`. Quando essa pasta existe, o programa usa essa pasta em modo portátil. Assim, basta colocar seus arquivos dentro dela e abrir o ScreenChurch.

Se a pasta portátil não existir, no Windows ela será criada em:

```text
Documentos/ScreenChurchData
```

Também é possível apontar para outro local usando a variável de ambiente:

```text
SCREENCHURCH_DATA_DIR
```

Estrutura criada automaticamente. A pasta `examples/` contém apenas exemplos e não é importada automaticamente:

```text
ScreenChurchData/
├── examples/
├── config/
│   └── projection_layout_presets.json
├── database/
│   └── screenchurch.db
├── bibles/
│   └── *.json
├── songs/
│   └── exports/
├── themes/
│   └── *.json
├── media/
│   ├── images/
│   ├── videos/
│   └── backgrounds/
│       ├── images/
│       └── videos/
├── services/
├── exports/
│   ├── presets/
│   ├── songs/
│   └── services/
└── backups/
```

### 2. O que vai para SQLite e o que vai para pastas

O banco local fica em:

```text
ScreenChurchData/database/screenchurch.db
```

Ele armazena:

- biblioteca de mídias;
- músicas e slides;
- índice das Bíblias importadas;
- base para configurações futuras.

Arquivos grandes continuam em pastas:

- vídeos em `media/videos/`;
- imagens em `media/images/`;
- fundos em `media/backgrounds/images/` e `media/backgrounds/videos/`;
- Bíblias JSON em `bibles/`;
- cultos salvos em `services/`;
- temas em `themes/`.

Os caminhos são salvos de forma relativa à pasta **ScreenChurchData** sempre que possível. Isso facilita copiar a pasta inteira para outro computador sem quebrar os vínculos.

### 3. Bíblia em JSON

O importador aceita o formato JSON usado pelo projeto **damarals/biblias**, que disponibiliza Bíblias em português em USX, SQLite e JSON. O formato JSON é tratado como lista de livros com abreviação e capítulos, por exemplo:

```json
[
  {
    "abbrev": "gn",
    "chapters": [
      ["No princípio criou Deus os céus e a terra."]
    ]
  }
]
```

Também continua aceitando o formato nativo do ScreenChurch:

```json
{
  "version": "ACF",
  "books": [
    {
      "name": "Gênesis",
      "chapters": [
        {
          "number": 1,
          "verses": [
            {"number": 1, "text": "No princípio criou Deus os céus e a terra."}
          ]
        }
      ]
    }
  ]
}
```

Você pode simplesmente copiar os arquivos `.json` para:

```text
ScreenChurchData/bibles/
```

e depois usar **Arquivo > Atualizar biblioteca**. Ao importar pelo menu, o arquivo também é copiado para essa pasta.

Observação: traduções bíblicas podem ter direitos autorais. O ScreenChurch fornece o importador; cada igreja deve usar versões autorizadas.

### 4. Temas, fundos e músicas

Coloque letras `.txt` ou pacotes `.json` de músicas em:

```text
ScreenChurchData/songs/
```

Depois use **Arquivo > Atualizar biblioteca**. O programa lê os arquivos, importa para o SQLite e preserva as edições feitas dentro do app.

Na edição de músicas:

- a letra é digitada ou colada em texto puro;
- uma linha em branco cria um novo slide;
- cada música pode ter fundo padrão com imagem ou vídeo;
- cada slide pode ter fundo próprio com imagem ou vídeo.

Você pode colocar fundos diretamente em:

```text
ScreenChurchData/media/backgrounds/images/
ScreenChurchData/media/backgrounds/videos/
```

e usar **Arquivo > Atualizar biblioteca**. Quando você escolhe uma imagem ou vídeo de fora da pasta de dados, o arquivo é copiado para essas mesmas pastas.

Mídias comuns podem ser colocadas diretamente ou adicionadas pela aba Mídias:

```text
ScreenChurchData/media/images/
ScreenChurchData/media/videos/
```


### 5. Pesquisa online de músicas

O menu **Letras → Pesquisar músicas online...** e o botão **🌐** da aba Letras abrem uma janela de pesquisa assistida.

Fluxo recomendado:

```text
1. Digite título, artista ou trecho.
2. Marque se deseja buscar por Título, Artista e/ou Letra.
3. Clique em 🔎 Pesquisar para listar links ou em 🌐 Abrir busca para pesquisar no navegador.
4. Selecione o resultado; o título/artista são preenchidos automaticamente quando possível.
5. Duplo clique no resultado abre o link no navegador quando a letra ainda está vazia; se já houver letra colada, abre direto no editor.
6. Copie a letra autorizada e clique em 📋 Colar área de transferência.
7. Use 🧩 Formatar slides para separar em 2 ou 4 linhas, se desejar.
8. Clique em ✏ Abrir em edição para carregar a música no editor completo.
9. Revise título, artista, letra, slides e fundos; depois salve a música.
```

O botão **✅ Salvar direto** continua disponível para casos simples. O botão **✏ Abrir em edição** é o fluxo recomendado, pois abre a mesma janela de edição de músicas com o texto puro à esquerda e os slides gerados automaticamente por linhas em branco.

O ScreenChurch **não copia letras automaticamente** de sites de terceiros. A janela foi feita para auxiliar a busca e o cadastro local, mantendo a igreja responsável por usar somente conteúdos próprios, de domínio público ou devidamente licenciados/autorizados.

### 6. Cultos e backups

Os cultos salvos usam `.screenchurch.json` e o local padrão é:

```text
ScreenChurchData/services/
```

No menu **Arquivo**, há ações para:

- abrir a pasta de dados;
- criar backup ZIP da pasta **ScreenChurchData**.

Para preservar o sistema da igreja, faça backup periódico dessa pasta.

### 7. Conceitos de operação

| Conceito | Função |
|---|---|
| **Projeção** | Abre ou fecha a janela de saída no monitor/projetor. |
| **Parte** | Uma divisão da saída: Parte 1, Parte 2, Parte 3 etc. |
| **Destino** | Parte que receberá mídia, letra, Bíblia ou item do culto. |
| **Prévia** | Carrega o conteúdo no painel do operador sem exibir no telão. |
| **Ao vivo** | Conteúdo que está sendo exibido na saída real do telão. |

Fluxo rápido:

```text
1. Escolha o monitor/projetor.
2. Escolha ou ajuste o layout.
3. Em Mídias, Letras, Bíblia ou Culto, escolha o destino no próprio módulo.
4. Use 👁 para prévia ou 📡 para enviar direto ao vivo.
```

### 8. Vídeos e codecs

Formatos de imagem:

```text
.png, .jpg, .jpeg, .bmp, .gif
```

Formatos de vídeo:

```text
.mp4, .avi, .mov, .wmv, .mkv, .flv
```

Formato recomendado:

```text
MP4 com vídeo H.264 e áudio AAC
```

A reprodução usa **VLC** como backend principal. Instale o **VLC Media Player 64-bit** no Windows.

### 9. Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Instale também o **VLC Media Player 64-bit**.

### 10. Execução

```bash
python screenChurch.py
```

### 11. Build Windows

```powershell
.\build_windows.ps1
```

### 11. Atalhos

```text
F5/F11      Iniciar/parar projeção
Ctrl+B      Abrir Bíblia
Esc         Blackout geral
Ctrl+Enter  Enviar parte selecionada ao vivo
Ctrl+,      Ajustes de layout/partes
Alt+1..9    Selecionar parte
Ctrl+S      Salvar culto
Ctrl+O      Abrir culto
```

---

## EN

### 1. Storage architecture

ScreenChurch now stores user data outside the application code in a local folder named **ScreenChurchData**.

This ZIP already includes a **ScreenChurchData/** folder next to the `.py` files. When this folder exists, the program uses it in portable mode. Put your files there and open ScreenChurch.

If the portable folder does not exist, on Windows it is created at:

```text
Documents/ScreenChurchData
```

You may override it with the environment variable:

```text
SCREENCHURCH_DATA_DIR
```

Automatically created structure. The `examples/` folder contains samples only and is not imported automatically:

```text
ScreenChurchData/
├── examples/
├── config/
│   └── projection_layout_presets.json
├── database/
│   └── screenchurch.db
├── bibles/
│   └── *.json
├── songs/
│   └── exports/
├── themes/
│   └── *.json
├── media/
│   ├── images/
│   ├── videos/
│   └── backgrounds/
│       ├── images/
│       └── videos/
├── services/
├── exports/
│   ├── presets/
│   ├── songs/
│   └── services/
└── backups/
```

### 2. SQLite and file folders

The local database is stored at:

```text
ScreenChurchData/database/screenchurch.db
```

It stores:

- media library index;
- songs and slides;
- imported Bible index;
- foundation for future configuration data.

Large files remain in folders:

- videos in `media/videos/`;
- images in `media/images/`;
- backgrounds in `media/backgrounds/images/` and `media/backgrounds/videos/`;
- Bible JSON files in `bibles/`;
- saved services in `services/`;
- themes in `themes/`.

Paths are stored relative to **ScreenChurchData** whenever possible, making backup and migration easier.

### 3. Bible JSON

The importer supports the JSON format used by **damarals/biblias**, which provides Portuguese Bibles in USX, SQLite and JSON. The JSON format is handled as a list of books with abbreviation and chapters, for example:

```json
[
  {
    "abbrev": "gn",
    "chapters": [
      ["In the beginning God created the heavens and the earth."]
    ]
  }
]
```

The native ScreenChurch format is also supported.

When a Bible is imported, the file is copied to:

```text
ScreenChurchData/bibles/
```

Note: Bible translations may be copyrighted. ScreenChurch provides the importer; each church should use authorized versions.

### 4. Themes, backgrounds and songs

Place `.txt` lyrics or `.json` song packages in:

```text
ScreenChurchData/songs/
```

Then use **File > Refresh library**. The program reads the files, imports them into SQLite and preserves edits made inside the app.

In the song editor:

- lyrics are typed or pasted as plain text;
- a blank line creates a new slide;
- each song may have a default image or video background;
- each slide may have its own image or video background.

Selected backgrounds are copied to:

```text
ScreenChurchData/media/backgrounds/images/
ScreenChurchData/media/backgrounds/videos/
```

Common media added in the Media tab are copied to:

```text
ScreenChurchData/media/images/
ScreenChurchData/media/videos/
```


### 5. Online song search

The **Lyrics → Search songs online...** menu and the **🌐** button in the Lyrics tab open an assisted web-search dialog.

Recommended workflow:

```text
1. Type the title, artist or a lyric excerpt.
2. Choose whether to search by Title, Artist and/or Lyrics.
3. Click 🔎 Search to list links or 🌐 Open search to use the browser.
4. Select a result; title/artist are filled automatically when possible.
5. Double-clicking a result opens the link in the browser when the lyrics field is still empty; if lyrics are already pasted, it opens the editor.
6. Copy authorized lyrics and click 📋 Paste clipboard.
7. Use 🧩 Format slides to split the text into 2 or 4 lines, if needed.
8. Click ✏ Open in editor to load the song into the full song editor.
9. Review title, artist, lyrics, slides and backgrounds; then save the song.
```

The **✅ Save directly** button remains available for simple cases. The recommended workflow is **✏ Open in editor**, because it opens the same song editor window with plain text on the left and slides generated automatically from blank lines.

ScreenChurch **does not automatically copy lyrics** from third-party websites. The dialog helps with discovery and local registration; each church remains responsible for using only original, public-domain or properly licensed/authorized content.

### 6. Services and backups

Saved services use `.screenchurch.json`, and the default location is:

```text
ScreenChurchData/services/
```

The **File** menu includes actions to:

- open the data folder;
- create a ZIP backup of **ScreenChurchData**.

Back up this folder regularly to preserve the church library.

### 7. Operation concepts

| Concept | Meaning |
|---|---|
| **Projection** | Opens or closes the output window on the projector/monitor. |
| **Part** | One division of the output: Part 1, Part 2, Part 3, etc. |
| **Target** | The part that will receive media, lyrics, Bible text or service items. |
| **Preview** | Loads content in the operator panel without showing it on the projector. |
| **Live** | Content currently shown on the real projection output. |

Fast workflow:

```text
1. Select the projector/monitor.
2. Select or adjust the layout.
3. In Media, Lyrics, Bible or Service, choose the target inside the module.
4. Use 👁 for preview or 📡 to send directly live.
```

### 7. Video and codecs

Image formats:

```text
.png, .jpg, .jpeg, .bmp, .gif
```

Video formats:

```text
.mp4, .avi, .mov, .wmv, .mkv, .flv
```

Recommended format:

```text
MP4 with H.264 video and AAC audio
```

Video playback uses **VLC** as the main backend. Install **VLC Media Player 64-bit** on Windows.

### 9. Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Also install **VLC Media Player 64-bit**.

### 10. Run

```bash
python screenChurch.py
```

### 11. Windows build

```powershell
.\build_windows.ps1
```

### 11. Shortcuts

```text
F5/F11      Start/stop projection
Ctrl+B      Open Bible
Esc         Global blackout
Ctrl+Enter  Send selected part live
Ctrl+,      Layout/part settings
Alt+1..9    Select part
Ctrl+S      Save service
Ctrl+O      Open service
```
