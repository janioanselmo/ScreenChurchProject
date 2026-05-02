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

A operação agora usa um fluxo único para evitar envios duplicados:

- **▶ Projetar**: apenas abre ou fecha a janela do telão/projetor; não envia conteúdo.
- **Abas Mídias, Letras, Bíblia e Culto**: apenas preparam conteúdo na prévia da parte escolhida.
- **⬆ Parte**: envia somente a parte selecionada para o ao vivo.
- **⬆⬆ Tudo**: envia todas as partes preparadas para o ao vivo.
- **Ao vivo**: é apenas status do que está na saída real.

Se o conteúdo da prévia já estiver ao vivo, o ScreenChurch não reenviará a mesma parte, evitando resets ou duplicação de vídeo/texto.

Para vídeos, o envio ao vivo preserva o ponto atual da prévia. Se você assistir 10 ou 15 segundos na visualização e depois usar **⬆ Parte**, **⬆⬆ Tudo** ou **▶ Projetar**, a saída sincroniza com a mesma posição/estado. O **áudio válido é sempre o da prévia do operador**; a janela de projeção fica visual-only/silenciada para evitar áudio duplicado.

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

The operator flow now uses a single live-send path to avoid duplicated sends:

- **▶ Project**: only opens or closes the projector/output window; it does not send content.
- **Media, Lyrics, Bible and Service tabs**: only prepare content in the selected part preview.
- **⬆ Part**: sends only the selected part live.
- **⬆⬆ All**: sends all prepared parts live.
- **Live**: only shows the current real output status.

If the preview content is already live, ScreenChurch skips the duplicated send to avoid resetting videos or duplicating text.

For videos, live sending preserves the current preview position. If you watch 10 or 15 seconds in the operator preview and then use **⬆ Part**, **⬆⬆ All** or **▶ Project**, the output synchronizes to the same position/state. The **operator preview is always the valid audio source**; the projection window is visual-only/muted to prevent duplicated audio.

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
Esc         Global blackout
Ctrl+Enter  Send selected part live
Ctrl+,      Layout/part settings
Alt+1..9    Select part
Ctrl+S      Save service
Ctrl+O      Open service
```


### Fluxo seguro de vídeo, áudio e blackout

- A prévia do operador é a fonte principal de áudio.
- A janela de projeção fica sempre sem áudio e acompanha visualmente o vídeo enviado ao vivo.
- Os comandos Play, Pause, Stop e busca de tempo atuam primeiro na prévia. Se o mesmo vídeo estiver ao vivo, a projeção é sincronizada com a posição e o estado da prévia.
- O botão Projetar apenas abre ou fecha a janela do telão; ele não duplica áudio.
- Os botões Enviar parte e Enviar tudo copiam a prévia para a projeção sem criar uma segunda fonte de áudio.
- O Blackout apenas oculta ou revela a imagem na projeção. Ele não pausa, reinicia, silencia ou altera o vídeo da prévia.

### Safe video, audio, and blackout flow

- The operator preview is the main audio source.
- The projection window is always muted and follows the live video visually.
- Play, Pause, Stop, and seek commands act on the preview first. If the same video is live, the projection is synchronized to the preview position and state.
- The Project button only opens or closes the output window; it does not duplicate audio.
- Send part and Send all copy the preview to the projection without creating a second audio source.
- Blackout only hides or reveals the projection image. It does not pause, restart, mute, or change the preview video.
