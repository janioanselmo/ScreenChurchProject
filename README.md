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


### 1.1. Estrutura dos arquivos do código

A interface foi reorganizada para reduzir o acoplamento do arquivo principal. O arquivo `main_window.py` agora concentra a montagem geral da janela e delega módulos específicos para arquivos separados:

```text
app.py                         inicializa o QApplication
screenChurch.py                ponto de entrada do programa
main_window.py                 janela principal e fluxo geral da interface
bible_dialogs.py               janela da Bíblia e busca rápida sequencial
bible_library.py               importação, normalização e busca bíblica
song_dialogs.py                pesquisa online e editor visual de músicas
song_library.py                biblioteca, importação e projeção de músicas
data_storage.py                ScreenChurchData, SQLite, backups e indexação
media_widget.py                componente de imagem/vídeo/texto por painel
projection_window.py           janela real de projeção
projection_settings_dialog.py  configuração de partes/layouts
preview_dialog.py              pré-visualização simples
constants.py                   constantes globais
```

Essa separação facilita manutenção, testes manuais e novos updates sem concentrar todos os recursos em um único arquivo.


#### Correção pós-refatoração

Após a separação dos módulos, foram revisados os imports entre `song_library.py`, `song_dialogs.py`, `bible_library.py`, `bible_dialogs.py` e `data_storage.py`. Os botões **Nova música**, **Editar música** e **Pesquisar músicas online** dependem desses módulos e agora possuem os imports explícitos necessários para evitar encerramento abrupto da aplicação.


#### Correção de persistência do editor visual de músicas

O editor visual de músicas salva junto com cada música:

- caixa de texto em normal, maiúsculo ou minúsculo;
- alinhamento;
- tamanho e cor da fonte;
- caixa atrás da letra e sua cor;
- fundo padrão da música em imagem ou vídeo;
- fundo individual por slide em imagem ou vídeo.

Essas informações ficam gravadas no SQLite dentro de `ScreenChurchData/database/screenchurch.db` e são carregadas novamente na lista de músicas e na projeção.

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


Mapeamento automático de versões do projeto `damarals/biblias`:

| Sigla | Nome exibido no ScreenChurch |
|---|---|
| ACF | ACF - Almeida Corrigida e Fiel |
| ARA | ARA - Almeida Revista e Atualizada |
| ARC | ARC - Almeida Revista e Corrigida |
| AS21 | AS21 - Almeida Século XXI |
| JFAA | JFAA - Almeida Atualizada |
| KJA | KJA - King James Atualizada |
| KJF | KJF - King James Fiel |
| NAA | NAA - Nova Almeida Atualizada |
| NBV | NBV - Nova Bíblia Viva |
| NTLH | NTLH - Nova Tradução na Linguagem de Hoje |
| NVI | NVI - Nova Versão Internacional |
| NVT | NVT - Nova Versão Transformadora |
| TB | TB - Tradução Brasileira |

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
- o primeiro slide é criado automaticamente com o título completo da música e, na segunda linha, o autor/artista;
- os slides seguintes exibem somente a letra, sem rodapé automático;
- essa regra vale para música criada manualmente, música editada, importação TXT/JSON e busca online;
- a janela de edição mostra dados, letra e prévias visuais na mesma tela;
- os botões superiores ajustam caixa alta/baixa, alinhamento, tamanho da fonte, cor da letra e caixa de texto;
- as prévias dos slides são atualizadas em tempo real;
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
3. Clique em 🔎 Pesquisar para listar os resultados dentro do ScreenChurch.
4. Selecione um resultado; o título/artista são preenchidos automaticamente quando possível.
5. Dê duplo clique no resultado ou clique em ⬇ Carregar letra.
6. O ScreenChurch tenta carregar a letra em texto puro e abrir diretamente o editor da música.
7. A letra entra no editor com a regra: linha em branco = novo slide.
8. Revise título, artista, letra, slides e fundos; depois salve a música.
```

O botão **✏ Carregar na edição** usa o mesmo fluxo do duplo clique: tenta buscar a letra do resultado selecionado e abre o editor completo. O botão **✅ Salvar direto** continua disponível para casos simples quando a letra já estiver no campo de texto.

Se um site bloquear a leitura automática ou retornar conteúdo incompatível, use **🌐 Abrir busca** como alternativa, copie a letra autorizada manualmente, clique em **📋 Colar área de transferência** e depois carregue na edição. A importação pela área de transferência possui proteção extra: se o conteúdo copiado parecer ser caminho de arquivo, URL, lista de arquivos do projeto, log ou texto técnico, o ScreenChurch bloqueia a importação para evitar que informações sem sentido sejam carregadas como letra.

A responsabilidade de uso das letras continua sendo da igreja/operador. Use apenas conteúdos próprios, de domínio público ou devidamente licenciados/autorizados.

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
4. Use 👁 para preparar na prévia. Para ir ao telão, use somente a barra superior: **⬆ Parte** ou **⬆⬆ Tudo**.
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


### 9. Estilo visual da Bíblia

A janela da Bíblia usa **sigla + nome completo** das versões importadas, como **NVI - Nova Versão Internacional** e **ACF - Almeida Corrigida e Fiel**, em vez de mostrar apenas siglas. Para arquivos do projeto `damarals/biblias`, o ScreenChurch reconhece automaticamente as siglas `ACF`, `ARA`, `ARC`, `AS21`, `JFAA`, `KJA`, `KJF`, `NAA`, `NBV`, `NTLH`, `NVI`, `NVT` e `TB`.

Os versículos possuem a mesma lógica visual das letras:

```text
Aa / AA / aa     caixa normal, maiúscula ou minúscula
☰ / ≡ / ☷       alinhamento à esquerda, centralizado ou justificado
A− / A+          diminuir ou aumentar fonte
🎨               cor da letra
▣ / ◼            caixa atrás do texto e cor da caixa
🖼 / 🎞 / 🚫     imagem de fundo, vídeo de fundo ou remover fundo
```

Essas alterações são aplicadas em tempo real nos versículos bíblicos que já estão na prévia ou ao vivo.

### 10. Prévia reduzida e projeção real

Os painéis da tela principal são apenas uma **prévia reduzida para operação**. O tamanho real da projeção continua sendo definido em **Layout → Ajustes de partes...** e é aplicado somente na janela do telão/projetor.

Exemplo:

```text
Prévia do operador: menor, apenas para visualização
Projeção real: 640×1080, 960×1080, 1920×1080 ou outro tamanho configurado
```

### 11. Busca rápida da Bíblia

A janela de localização da Bíblia agora trabalha em etapas, semelhante ao fluxo de operação do Holyrics:

```text
Livro → Enter → Capítulo → Enter → Versículo → Enter
```

Enquanto você digita o livro, o ScreenChurch mostra sugestões como `Josué`, `Joel`, `Jonas`, `João` e `Jó`. Para livros numerados, digitar `1`, `2` ou `3` mantém a busca no estágio de livro e lista as opções correspondentes, como `1 Samuel`, `1 Reis`, `1 Crônicas`, `1 Coríntios`, `1 Tessalonicenses`, `1 Timóteo`, `1 Pedro` e `1 João`. Use as setas para alternar a sugestão selecionada e pressione **Enter** para confirmar.

Depois de confirmar o livro, o programa libera apenas capítulos válidos daquele livro. Exemplo: se o livro possuir 21 capítulos, o capítulo `0` e qualquer valor acima de `21` são bloqueados. O mesmo vale para os versículos do capítulo selecionado.

Atalhos da busca rápida:

```text
Enter      confirma a etapa atual
Backspace  corrige ou volta uma etapa
Setas      alternam a sugestão de livro
Esc        cancela a busca rápida
```



### Fluxo padronizado de projeção

A operação usa o botão **▶ Projetar** como comando principal para reduzir conflitos de áudio/vídeo.

- **▶ Projetar**: abre/fecha a janela do telão e espelha todas as partes configuradas.
- **Abas Mídias, Letras, Bíblia e Culto**: preparam conteúdo na prévia da parte escolhida.
- **Blackout individual**: oculta somente a parte desejada, sem pausar ou reiniciar vídeo.
- **Ao vivo**: é apenas status do que está na saída real.

Não existe mais checkbox individual de projeção por parte. Ao projetar, todas as partes do layout são exibidas; para ocultar uma parte específica, use o **Blackout** daquela parte.

Para vídeos, o botão **▶ Projetar** preserva o ponto atual da prévia. A prévia do operador permanece como fonte de áudio; a projeção usa um player próprio sempre sem áudio, sincronizado com a posição/estado da prévia. Essa arquitetura evita áudio duplicado e também evita a tela preta causada pela troca da superfície VLC enquanto o vídeo já está tocando.

### 12. Navegação ao vivo por teclado

Quando a janela de projeção estiver aberta e uma **letra** ou **Bíblia** estiver ao vivo, as setas do teclado navegam o conteúdo projetado:

```text
Seta direita / Seta baixo / PageDown   avança slide da música ou versículo bíblico
Seta esquerda / Seta cima / PageUp     retrocede slide da música ou versículo bíblico
```

A navegação só atua em conteúdos do tipo **letra** ou **Bíblia** e somente com a projeção ativa. Imagens e vídeos não são alterados por esses atalhos.

### 12. Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> Observação: se estiver usando Python 3.13, mantenha `PyInstaller>=6.15.0,<7.0`. Versões antigas como `PyInstaller==6.0` não são compatíveis com Python 3.13.

Instale também o **VLC Media Player 64-bit**.

### 11. Execução

```bash
python screenChurch.py
```

### 12. Build Windows

```powershell
.\build_windows.ps1
```

### 13. Atalhos

```text
F5/F11      Iniciar/parar projeção
Ctrl+B      Abrir Bíblia
←/→ ↑/↓     Navegar letra/Bíblia ao vivo
Esc         Fecha/cancela busca rápida quando aplicável
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


### Visual song editor persistence fix

The visual song editor stores each song with:

- normal, uppercase or lowercase text mode;
- alignment;
- font size and color;
- lyric text box and its color;
- default song background as image or video;
- individual slide background as image or video.

These settings are stored in SQLite at `ScreenChurchData/database/screenchurch.db` and are restored in the song list and projection.

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


Automatic version mapping for the `damarals/biblias` project:

| Abbreviation | Display name in ScreenChurch |
|---|---|
| ACF | ACF - Almeida Corrigida e Fiel |
| ARA | ARA - Almeida Revista e Atualizada |
| ARC | ARC - Almeida Revista e Corrigida |
| AS21 | AS21 - Almeida Século XXI |
| JFAA | JFAA - Almeida Atualizada |
| KJA | KJA - King James Atualizada |
| KJF | KJF - King James Fiel |
| NAA | NAA - Nova Almeida Atualizada |
| NBV | NBV - Nova Bíblia Viva |
| NTLH | NTLH - Nova Tradução na Linguagem de Hoje |
| NVI | NVI - Nova Versão Internacional |
| NVT | NVT - Nova Versão Transformadora |
| TB | TB - Tradução Brasileira |

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
- the first slide is created automatically with the full song title and, on the second line, the author/artist;
- the following slides show lyrics only, without an automatic footer;
- this rule applies to manually created songs, edited songs, TXT/JSON imports and online search;
- the editor window shows metadata, lyrics and visual slide previews in the same screen;
- top toolbar buttons adjust text case, alignment, font size, text color and text box display;
- slide previews update in real time;
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
3. Click 🔎 Search to list results inside ScreenChurch.
4. Select a result; title/artist are filled automatically when possible.
5. Double-click the result or click ⬇ Load lyrics.
6. ScreenChurch tries to load the lyrics as plain text and open the full song editor.
7. The editor uses the rule: blank line = new slide.
8. Review title, artist, lyrics, slides and backgrounds; then save the song.
```

The **✏ Open in editor** button uses the same flow as double-click: it tries to fetch the selected result's lyrics and opens the full editor. The **✅ Save directly** button remains available for simple cases when lyrics are already in the text field.

If a website blocks automatic reading or returns incompatible content, use **🌐 Open search** as a fallback, manually copy authorized lyrics, click **📋 Paste clipboard**, and then open the editor. Clipboard import has an extra safety check: if the copied content looks like file paths, URLs, project file lists, logs or technical text, ScreenChurch blocks the import so meaningless content is not loaded as song lyrics.

Lyrics usage remains the responsibility of the church/operator. Use only original, public-domain or properly licensed/authorized content.

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
4. Use 👁 to prepare the preview. To send to the projector, use only the top toolbar: **⬆ Part** or **⬆⬆ All**.
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


### 9. Bible visual style

The Bible window displays **abbreviation + full name** for imported versions, such as **NVI - Nova Versão Internacional** and **ACF - Almeida Corrigida e Fiel**, instead of showing only abbreviations. For files from the `damarals/biblias` project, ScreenChurch automatically recognizes the abbreviations `ACF`, `ARA`, `ARC`, `AS21`, `JFAA`, `KJA`, `KJF`, `NAA`, `NBV`, `NTLH`, `NVI`, `NVT` and `TB`.

Bible verses now use the same visual editing concept as lyrics:

```text
Aa / AA / aa     normal, uppercase or lowercase
☰ / ≡ / ☷       left, center or justified alignment
A− / A+          decrease or increase font size
🎨               text color
▣ / ◼            text box and text box color
🖼 / 🎞 / 🚫     image background, video background or clear background
```

These changes are applied in real time to Bible verses already loaded in preview or live output.

### 10. Reduced preview and real projection size

The panels in the main window are only a **reduced operator preview**. The real projection size remains defined in **Layout → Ajustes de partes...** and is applied only to the projector/output window.

Example:

```text
Operator preview: smaller, only for visual monitoring
Real projection: 640×1080, 960×1080, 1920×1080 or any configured size
```

### 11. Fast Bible search

The Bible locator now works step by step, similar to a church presentation workflow:

```text
Book → Enter → Chapter → Enter → Verse → Enter
```

While you type the book, ScreenChurch shows suggestions such as `Josué`, `Joel`, `Jonas`, `João` and `Jó`. For numbered books, typing `1`, `2` or `3` keeps the dialog in the book stage and lists matching options such as `1 Samuel`, `1 Reis`, `1 Crônicas`, `1 Coríntios`, `1 Tessalonicenses`, `1 Timóteo`, `1 Pedro` and `1 João`. Use the arrow keys to change the selected suggestion and press **Enter** to confirm.

After the book is confirmed, only valid chapters for that book are accepted. Example: if the book has 21 chapters, chapter `0` and any value above `21` are blocked. The same validation is applied to verses in the selected chapter.

Fast search shortcuts:

```text
Enter      confirm current step
Backspace  correct or go back one step
Arrows     switch selected book suggestion
Esc        cancel fast search
```



### Standardized projection flow

The operator flow uses **▶ Project** as the main command to reduce audio/video conflicts:

- **▶ Project**: opens/closes the projector/output window and mirrors all configured parts.
- **Media, Lyrics, Bible and Service tabs**: prepare content in the selected part preview.
- **Per-part Blackout**: hides only the selected part without pausing or restarting video.
- **Live**: only shows the current real output status.

There is no longer a per-part projection checkbox. When projecting, every part in the layout is shown; to hide a specific part, use that part's **Blackout** button.

For videos, **▶ Project** preserves the current preview position. If you watch 10 or 15 seconds in the operator preview and then project, the output synchronizes to the same position/state. The **operator preview remains the only audio source**; the projection only mirrors the video on the output screen without creating a second audio output. On some Windows computers, VLC may open the new video surface as black; ScreenChurch therefore performs an internal decoder refresh at the same timestamp.

### 12. Live keyboard navigation

When the projection window is open and **lyrics** or **Bible text** is live, the keyboard arrows navigate the projected content:

```text
Right arrow / Down arrow / PageDown   next song slide or Bible verse
Left arrow / Up arrow / PageUp        previous song slide or Bible verse
```

Navigation only affects **lyrics** and **Bible** text while projection is active. Images and videos are not changed by these shortcuts.

### 12. Installation

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

### 12. Windows build

```powershell
.\build_windows.ps1
```

### 13. Shortcuts

```text
F5/F11      Start/stop projection
Ctrl+B      Open Bible
←/→ ↑/↓     Navigate live lyrics/Bible
Esc         Close/cancel quick search when applicable
Ctrl+,      Layout/part settings
Alt+1..9    Select part
Ctrl+S      Save service
Ctrl+O      Open service
```


### Fluxo seguro de vídeo, áudio e blackout

- A prévia do operador é a fonte principal de áudio.
- Com a projeção ativa, a saída projetada acompanha visualmente o mesmo ponto/estado da prévia, mas não assume o áudio.
- Os comandos Play, Pause, Stop e busca de tempo atuam primeiro na prévia. Se o mesmo vídeo estiver ao vivo, a projeção é sincronizada com a posição e o estado da prévia.
- O botão Projetar abre/fecha o telão e espelha todas as partes configuradas.
- Não existem mais comandos separados de Enviar parte/Enviar tudo na barra superior.
- O Blackout individual apenas oculta ou revela uma parte da projeção. Ele não pausa, reinicia, silencia ou altera o vídeo da prévia.

### Safe video, audio, and blackout flow

- The operator preview is the main audio source.
- The operator preview remains the only audio source; projection mirrors the visual output.
- Play, Pause, Stop, and seek commands act on the preview first. If the same video is live, the projection is synchronized to the preview position and state.
- The Project button opens/closes the output window and mirrors all configured parts.
- There are no separate Send part/Send all commands in the top bar.
- Per-panel blackout only hides or reveals one projection part. It does not pause, restart, mute, or change the preview video.


## Fluxo simplificado de projeção (v40)

A operação foi simplificada para reduzir conflitos de áudio/vídeo:

- **Projetar** é o comando principal: ele abre/fecha o telão e espelha todas as partes configuradas.
- Os checkboxes individuais **Projetar** foram removidos dos cards das partes.
- A barra superior não possui mais **Enviar parte**, **Enviar tudo**, **Blackout geral** nem atalho da Bíblia.
- O **Preview** é o único player real de vídeo e áudio.
- A projeção acompanha visualmente o mesmo instante do Preview, sem criar novo play e sem duplicar áudio.
- Use o blackout individual de cada parte quando quiser ocultar uma área específica.

## Simplified projection flow (v40)

The operation flow was simplified to avoid audio/video conflicts:

- **Project** is the main command: it opens/closes the output screen and mirrors all configured parts.
- Per-part **Project** checkboxes were removed from the part cards.
- The top bar no longer has **Send part**, **Send all**, **Global blackout**, or a Bible shortcut.
- The **Preview** is the only real video/audio player.
- Projection visually follows the same Preview instant, without starting another playback and without duplicated audio.
- Use each part blackout button when you need to hide a specific output area.

---

## v40 - Fluxo de vídeo com player único (Preview -> Projeção)

Nesta versão o fluxo de vídeo foi simplificado para evitar conflito de áudio entre a prévia e o telão.

Regra aplicada:

- o **Preview** é o único player real de vídeo e áudio;
- o botão **Projetar** não cria uma segunda reprodução;
- o botão **Projetar** apenas redireciona a saída visual do vídeo atual para a superfície de projeção;
- o vídeo não reinicia ao projetar;
- o vídeo não é mutado ao projetar;
- o áudio não é duplicado;
- ao fechar a projeção, a saída visual retorna para o Preview.

Comportamento esperado:

1. Carregue um vídeo em uma parte.
2. Dê Play no Preview.
3. Aguarde alguns segundos.
4. Clique em **Projetar**.
5. O telão passa a mostrar o mesmo vídeo no mesmo instante, sem novo play e sem duplicação de áudio.

Observação: durante a projeção de vídeo, o player real pertence ao Preview. Por isso, o controle Play/Pause/Stop continua sendo feito na área de operação.

---

## v40 - Single-player video flow (Preview -> Projection)

This version simplifies video playback to avoid audio conflicts between the operator preview and the projector output.

Applied rule:

- the **Preview** is the only real video/audio player;
- the **Project** button does not create a second playback instance;
- the **Project** button only redirects the current video output to the projection surface;
- the video does not restart when projected;
- the video is not muted when projected;
- audio is not duplicated;
- when projection is closed, video output returns to the Preview.

Expected behavior:

1. Load a video into a part.
2. Press Play in the Preview.
3. Wait a few seconds.
4. Click **Project**.
5. The projector shows the same video at the same instant, with no new playback and no duplicated audio.

Note: during video projection, the real player belongs to the Preview. Play/Pause/Stop controls remain in the operator area.


## v41 — Fluxo de projeção limpo

- O botão **Projetar** espelha todas as partes configuradas.
- Os checkboxes individuais de cada parte foram removidos.
- O controle individual que permanece em cada parte é apenas o **Blackout**.
- Para ocultar uma parte específica durante a projeção, use o botão de blackout daquela parte.
- A seleção da parte continua disponível ao clicar no card ou pelos seletores de destino dos módulos.

---

## v41 — Clean projection flow

- The **Project** button mirrors all configured parts.
- Individual per-part projection checkboxes were removed.
- The only per-part visibility control that remains is **Blackout**.
- To hide a specific part during projection, use that part's blackout button.
- Part selection is still available by clicking the card or using each module's target selector.

---

## v42 - Correção de superfície VLC ao projetar

- Mantém a arquitetura de player único: o Preview continua sendo o player real de áudio e vídeo.
- Corrige o caso em que o áudio tocava, mas a projeção ficava preta até o usuário pressionar Stop/Play.
- Ao alternar a saída visual do Preview para a projeção, o sistema faz um pequeno refresh interno da superfície VLC sem criar outro player, sem mutar e sem reiniciar o vídeo.
- O botão Projetar continua espelhando todas as partes configuradas.
- O Blackout por parte continua sendo o controle individual de visibilidade.

## v42 - VLC surface refresh when projecting

- Keeps the single-player architecture: Preview remains the real audio/video player.
- Fixes the case where audio kept playing but the projected output stayed black until Stop/Play was pressed.
- When moving the visual output from Preview to Projection, the app performs a small internal VLC surface refresh without creating another player, muting, or restarting the video.
- The Project button continues to mirror all configured parts.
- Per-part Blackout remains the individual visibility control.


### v44 — Projeção suave e barra de progresso

- A projeção mantém o conceito de player único: o vídeo do Preview é a fonte real.
- A troca para o telão não reinicia mais o decodificador VLC, evitando o repique visual.
- A barra de progresso agora respeita o arraste do mouse: enquanto o operador segura o slider, o sistema não força o retorno para o tempo antigo.
- Ao soltar o mouse, o novo tempo é confirmado e refletido na projeção ativa.
- `Projetar` continua sem criar segundo áudio e sem tocar outro player por cima do Preview.

### v44 — Smooth projection and progress bar

- Projection keeps the single-player concept: Preview remains the real video source.
- Switching to the output screen no longer restarts the VLC decoder, avoiding visible playback bumps.
- The progress bar now respects mouse dragging: while the operator holds the slider, the UI does not force it back to the old timestamp.
- Releasing the mouse commits the new timestamp and reflects it in the active projection.
- `Project` still does not create a second audio source or play another player over Preview.

### v45 — Edição de layouts, ícones e ativação da superfície VLC

- Adicionado botão **✏️** na barra superior para editar o layout selecionado.
- A edição permite renomear o preset e ajustar as dimensões das partes usando a mesma validação dos ajustes de layout.
- Ícones de limpeza foram padronizados para **🗑**, deixando a ação mais visível e consistente.
- A troca da superfície VLC ao clicar em **Projetar** recebeu uma ativação mais robusta para evitar tela preta na primeira projeção de um vídeo já em reprodução.
- Mantida a regra de player único: o Preview continua sendo a fonte real do vídeo/áudio, sem segundo áudio e sem reprodução duplicada.

### v45 — Layout editing, clearer icons and VLC surface activation

- Added a **✏️** button to the top toolbar to edit the selected layout preset.
- Editing allows renaming the preset and changing part dimensions with the same layout validation rules.
- Clear/delete icons were standardized to **🗑** for better visibility and consistency.
- VLC surface switching on **Project** now performs a stronger activation step to reduce black-screen cases on the first projection of an already playing video.
- The single-player rule remains: Preview is still the real video/audio source, with no duplicated audio and no second playback instance.


### v46 — Gerenciamento de layouts e projeção sem Stop/Play

- O botão de edição de layouts agora permite **Editar** ou **Remover** o preset selecionado.
- A primeira ativação da projeção recebeu ligação atrasada da superfície VLC para evitar tela preta sem usar Stop/Play interno.
- A regra permanece: **Preview é o player real de áudio/vídeo** e **Projetar apenas move a saída visual para o telão**.

### v46 — Layout management and projection without Stop/Play

- The layout edit button now allows editing or removing the selected preset.
- The first projection activation now delays VLC surface binding to avoid black output without using internal Stop/Play.
- The rule remains: **Preview is the real audio/video player** and **Project only moves the visual output to the screen**.

---

### v47 — Padronização dos ícones do editor de músicas

A janela **Editar música** recebeu uma padronização visual na barra superior:

- botões com tamanho fixo e aparência consistente;
- ícones alinhados ao mesmo padrão visual usado na Bíblia;
- botão de limpeza padronizado como **🗑**;
- indicadores de cor da letra e da caixa de texto agora usam borda colorida, evitando botões claros ou pouco visíveis;
- tooltips preservados para facilitar o uso.

A alteração é apenas visual/organizacional e não muda a lógica de salvamento, projeção ou reprodução.

### v47 — Song editor icon standardization

The **Edit song** window now has a standardized top toolbar:

- fixed-size buttons with consistent appearance;
- icons aligned with the same visual style used in the Bible window;
- clear/remove actions standardized as **🗑**;
- text color and text box color buttons now use colored borders, avoiding overly bright or unclear buttons;
- tooltips preserved for easier operation.

This is a visual/organization update only and does not change saving, projection or playback logic.


### v48 — Projeção com player sincronizado e editor de música mais limpo

- A projeção de vídeo voltou a usar um player próprio, porém sempre sem áudio.
- O Preview permanece como fonte de áudio e controle principal.
- A projeção sincroniza tempo e estado com o Preview, evitando áudio duplicado e tela preta ao clicar em **Projetar** com o vídeo já em execução.
- O slider do Preview continua controlando o tempo e a projeção acompanha em tempo real.
- A barra superior do **Editar música** foi reorganizada para concentrar os controles em uma única linha, no estilo da Bíblia/Holyrics.
- Os botões de fundo padrão e fundo por slide foram movidos para a barra superior.

### v48 — Synchronized projection player and cleaner song editor

- Video projection now uses its own player, but it is always muted.
- The Preview remains the audio source and main playback controller.
- Projection synchronizes time and state from Preview, avoiding duplicated audio and the black screen issue when projecting a video already playing.
- The Preview slider keeps controlling the video position and projection follows in real time.
- The **Edit song** top toolbar was reorganized to keep controls in one clean row, closer to the Bible/Holyrics style.
- Default-background and per-slide-background actions were moved to the top toolbar.

### v49 — Correção do áudio do Preview e botões claros no editor de músicas

- O Preview foi reforçado como a fonte principal de áudio.
- A Projeção continua usando player próprio sincronizado, porém sempre sem áudio.
- A política de áudio agora é aplicada após projetar, sincronizar, dar play, pausar, parar e mover a barra de progresso.
- A barra superior do **Editar música** agora usa ícones com texto curto para reduzir ambiguidade:
  - **🎨 A** para cor da letra;
  - **▣ Box** para ativar/desativar a caixa atrás da letra;
  - **🎨 Box** para cor da caixa;
  - **🖼 Música / 🎞 Música / 🗑 Música** para fundo padrão da música;
  - **🖼 Slide / 🎞 Slide / 🗑 Slide** para fundo do slide selecionado.
- Foram removidas as bordas coloridas grossas dos botões de cor, mantendo o estilo visual uniforme da barra.

### v49 — Preview audio fix and clearer song editor buttons

- The Preview is reinforced as the main audio source.
- Projection still uses its own synchronized player, but it is always silent.
- The audio policy is now applied after projecting, syncing, playing, pausing, stopping and seeking.
- The **Edit song** toolbar now uses icons with short labels to reduce ambiguity:
  - **🎨 A** for text color;
  - **▣ Box** for enabling/disabling the text box;
  - **🎨 Box** for text box color;
  - **🖼 Song / 🎞 Song / 🗑 Song** for the default song background;
  - **🖼 Slide / 🎞 Slide / 🗑 Slide** for the selected slide background.
- Thick colored borders were removed from color buttons, keeping the toolbar visually consistent.

### v50 — Correção de áudio contínuo no Preview

- A Projeção continua usando player próprio sincronizado, evitando a tela preta do VLC.
- O player da Projeção agora é inicializado sem saída de áudio (`--no-audio`), em vez de ficar alternando mute/volume durante a sincronização.
- O Preview permanece como a única fonte de áudio e não é mais afetado pelo player da Projeção.
- A política de áudio foi simplificada para evitar que o som do Preview só apareça ao pressionar Play repetidamente.
- A sincronização de vídeo continua preservando posição, play/pause e slider em tempo real.

### v50 — Continuous Preview audio fix

- Projection still uses its own synchronized player to avoid VLC black-screen issues.
- The Projection player is now created without audio output (`--no-audio`) instead of repeatedly toggling mute/volume during synchronization.
- Preview remains the only audio source and is no longer affected by the Projection player.
- The audio policy was simplified to avoid cases where Preview audio only came back after repeatedly pressing Play.
- Video synchronization still preserves position, play/pause state and real-time slider control.

### v51 — Dados do desenvolvedor na tela Sobre

- A opção **Ajuda → Sobre** agora exibe os dados do desenvolvedor:
  - Jânio Anselmo, Eng. Me
  - janio@ensa.com.br
  - +55 (48) 3017-1000

### v51 — Developer information in About dialog

- The **Help → About** dialog now displays the developer information:
  - Jânio Anselmo, Eng. Me
  - janio@ensa.com.br
  - +55 (48) 3017-1000
