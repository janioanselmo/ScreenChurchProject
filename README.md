# ScreenChurchProject

⛪ Aplicativo desktop em Python para exibir mídias em três áreas simultâneas, pensado para uso em telas de apoio, projeção ou organização visual em ambientes de igreja.

## 📌 Visão geral

O projeto usa **PyQt5** para criar uma janela com três painéis independentes. Cada painel pode carregar uma imagem ou vídeo a partir do computador, permitindo montar rapidamente uma tela tripla de exibição.

## ✨ Funcionalidades

- Interface gráfica desktop com PyQt5.
- Três áreas independentes de mídia.
- Carregamento individual de mídia para cada área.
- Suporte a imagens e vídeos.
- Reprodução automática de vídeos ao carregar o arquivo.
- Layout simples, direto e adequado para operação manual.

## 📁 Estrutura

| Arquivo | Descrição |
| --- | --- |
| `screenChurch.py` | Aplicação principal com interface PyQt5 |
| `requirements.txt` | Dependências Python do projeto |
| `LICENSE` | Licença do repositório |
| `.gitignore` | Regras de arquivos ignorados pelo Git |

## 🛠️ Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## ▶️ Execução

```powershell
python screenChurch.py
```

## 🖼️ Formatos suportados

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

## 🧪 Observações técnicas

- O projeto depende de `PyQt5>=5.15`.
- A reprodução de vídeo usa `QMediaPlayer` e `QVideoWidget`.
- O suporte real a codecs pode variar conforme o sistema operacional e os codecs instalados.
- O layout atual abre uma janela de `1440x480`, dividida em três painéis horizontais.
- Arquivos não suportados não são tratados com mensagem específica na versão atual.

## 🚧 Melhorias futuras

- Adicionar modo tela cheia.
- Permitir seleção de monitor/projetor.
- Adicionar botão para limpar mídia de cada painel.
- Exibir aviso amigável para formatos não suportados.
- Salvar e restaurar a última configuração usada.
- Adicionar atalhos de teclado para operação durante cultos/eventos.

## 📄 Licença

Consulte `LICENSE`.
