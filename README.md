# ps2opl

🇺🇸 [English](#english) | 🇧🇷 [Português](#português)

# English

`ps2opl` is a command-line utility written in Python for managing PlayStation 2 games and storage devices used with **Open PS2 Loader (OPL)**.

The project aims to provide a Linux-friendly command-line alternative for common OPL game-management tasks.

> **Project status:** early development / pre-alpha.

---

## Goals

The initial goal is to create a simple and reliable CLI capable of inspecting PlayStation 2 ISO images and preparing them for use with Open PS2 Loader.

Future versions are expected to support storage management, artwork, configuration files, Virtual Memory Cards (VMCs), and games larger than 4 GB on FAT32 devices.

---

## Planned features

### v0.1 — ISO identification

- Scan directories for PlayStation 2 ISO images
- Read `SYSTEM.CNF` directly from ISO images
- Detect the game ID:
  - `SLUS`
  - `SCUS`
  - `SLES`
  - `SCES`
  - `SLPS`
  - and others
- Read the game version
- Detect video mode (`NTSC` / `PAL`)
- Detect CD/DVD media
- Display ISO size
- Generate OPL-compatible filenames
- Rename ISO files
- Support `dry-run` operations

Example:

```text
Ben 10 - Protector of Earth (USA).iso
```

becomes:

```text
SLUS_216.61.Ben 10 - Protector of Earth.iso
```

---

### v0.2 — OPL storage management

Planned features:

- Detect OPL storage devices
- List installed games
- Validate the OPL directory structure
- Install games
- Remove games
- Detect incorrectly named ISOs
- Detect files larger than the FAT32 limit

Expected OPL directories include:

```text
ART/
CD/
CFG/
CHT/
DVD/
VMC/
```

---

### v0.3 — Large games and UL format

Planned features:

- Support games larger than 4 GB on FAT32
- Read and generate `ul.cfg`
- Split games
- Validate split files
- Reconstruct games when necessary

---

### v0.4 — Artwork and configuration

Planned features:

- Manage OPL artwork
- Detect missing covers
- Associate artwork with game IDs
- Read and write OPL configuration files

---

### v0.5 — Virtual Memory Cards

Planned features:

- List VMC files
- Create VMCs
- Associate VMCs with games
- Validate VMC files

---

## Requirements

- Python 3.11 or newer
- Linux

Other operating systems may be supported in the future.

---

## Development setup

Clone the repository:

```bash
git clone <repository-url>
cd ps2opl
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Upgrade `pip`:

```bash
python -m pip install --upgrade pip
```

Install the project in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

---

## Project structure

```text
ps2opl/
├── pyproject.toml
├── README.md
├── src/
│   └── ps2opl/
│       ├── __init__.py
│       ├── cli.py
│       ├── iso.py
│       ├── games.py
│       ├── naming.py
│       ├── storage.py
│       ├── covers.py
│       ├── config.py
│       └── ul.py
└── tests/
```

The project uses the Python `src` layout to keep package code separated from the other repository files.

---

## Command-line interface

After installation, the following command will be available:

```bash
ps2opl
```

Planned commands include:

```bash
ps2opl scan <path>
ps2opl list <path>
ps2opl info <iso>
ps2opl rename <path>
ps2opl install <iso> <device>
ps2opl check <device>
```

For example:

```bash
ps2opl info "Ben 10 - Protector of Earth (USA).iso"
```

Expected output:

```text
Title:       Ben 10 - Protector of Earth
Game ID:     SLUS_216.61
Version:     1.01
Video mode:  NTSC
Media:       DVD
Size:        3.40 GB

OPL filename:
SLUS_216.61.Ben 10 - Protector of Earth.iso
```

---

## Development

Run the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=ps2opl
```

Run the linter:

```bash
ruff check .
```

Automatically fix supported lint problems:

```bash
ruff check . --fix
```

---

## Safety

Game files should never be modified or overwritten without an explicit command from the user.

Operations that rename, move, remove, split, or otherwise modify files should perform validation and, whenever appropriate, provide a `dry-run` mode.

Example:

```bash
ps2opl rename /path/to/games --dry-run
```

---

## Legal notice

`ps2opl` is an independent open-source project and is not affiliated with or endorsed by Sony Interactive Entertainment or the Open PS2 Loader project.

Users are responsible for complying with applicable copyright laws and should use the software only with game images they are legally permitted to use.

---

## License

MIT License.

---

# Português

`ps2opl` é uma ferramenta de linha de comando escrita em Python para gerenciamento de jogos de PlayStation 2 e dispositivos de armazenamento utilizados com o **Open PS2 Loader (OPL)**.

O projeto tem como objetivo fornecer uma alternativa via linha de comando, amigável ao Linux, para tarefas comuns de gerenciamento de jogos e dispositivos utilizados pelo OPL.

> **Status do projeto:** desenvolvimento inicial / pré-alpha.

---

## Objetivos

O objetivo inicial é criar uma CLI simples e confiável capaz de inspecionar imagens ISO de jogos de PlayStation 2 e prepará-las para utilização com o Open PS2 Loader.

Versões futuras deverão oferecer suporte ao gerenciamento de dispositivos de armazenamento, capas, arquivos de configuração, cartões de memória virtuais (VMC) e jogos maiores que 4 GB em dispositivos FAT32.

---

## Funcionalidades planejadas

### v0.1 — Identificação de ISOs

- Procurar imagens ISO de PlayStation 2 em diretórios
- Ler o arquivo `SYSTEM.CNF` diretamente das imagens ISO
- Detectar o ID do jogo:
  - `SLUS`
  - `SCUS`
  - `SLES`
  - `SCES`
  - `SLPS`
  - entre outros
- Ler a versão do jogo
- Detectar o modo de vídeo (`NTSC` / `PAL`)
- Detectar mídia CD/DVD
- Exibir o tamanho da ISO
- Gerar nomes de arquivos compatíveis com OPL
- Renomear arquivos ISO
- Suportar operações em modo `dry-run`

Exemplo:

```text
Ben 10 - Protector of Earth (USA).iso
```

torna-se:

```text
SLUS_216.61.Ben 10 - Protector of Earth.iso
```

---

### v0.2 — Gerenciamento do armazenamento OPL

Funcionalidades planejadas:

- Detectar dispositivos de armazenamento utilizados pelo OPL
- Listar jogos instalados
- Validar a estrutura de diretórios do OPL
- Instalar jogos
- Remover jogos
- Detectar ISOs com nomes incorretos
- Detectar arquivos maiores que o limite do FAT32

Diretórios esperados do OPL incluem:

```text
ART/
CD/
CFG/
CHT/
DVD/
VMC/
```

---

### v0.3 — Jogos grandes e formato UL

Funcionalidades planejadas:

- Suportar jogos maiores que 4 GB em FAT32
- Ler e gerar `ul.cfg`
- Dividir jogos
- Validar arquivos divididos
- Reconstruir jogos quando necessário

---

### v0.4 — Capas e configurações

Funcionalidades planejadas:

- Gerenciar artes e capas utilizadas pelo OPL
- Detectar capas ausentes
- Associar artes aos IDs dos jogos
- Ler e escrever arquivos de configuração do OPL

---

### v0.5 — Cartões de memória virtuais

Funcionalidades planejadas:

- Listar arquivos VMC
- Criar VMCs
- Associar VMCs aos jogos
- Validar arquivos VMC

---

## Requisitos

- Python 3.11 ou superior
- Linux

Outros sistemas operacionais poderão ser suportados futuramente.

---

## Configuração do ambiente de desenvolvimento

Clone o repositório:

```bash
git clone <repository-url>
cd ps2opl
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente:

```bash
source .venv/bin/activate
```

Atualize o `pip`:

```bash
python -m pip install --upgrade pip
```

Instale o projeto em modo editável com as dependências de desenvolvimento:

```bash
pip install -e ".[dev]"
```

---

## Estrutura do projeto

```text
ps2opl/
├── pyproject.toml
├── README.md
├── src/
│   └── ps2opl/
│       ├── __init__.py
│       ├── cli.py
│       ├── iso.py
│       ├── games.py
│       ├── naming.py
│       ├── storage.py
│       ├── covers.py
│       ├── config.py
│       └── ul.py
└── tests/
```

O projeto utiliza o layout `src` do Python para manter o código do pacote separado dos demais arquivos do repositório.

---

## Interface de linha de comando

Após a instalação, o seguinte comando estará disponível:

```bash
ps2opl
```

Os comandos planejados incluem:

```bash
ps2opl scan <path>
ps2opl list <path>
ps2opl info <iso>
ps2opl rename <path>
ps2opl install <iso> <device>
ps2opl check <device>
```

Por exemplo:

```bash
ps2opl info "Ben 10 - Protector of Earth (USA).iso"
```

Saída esperada:

```text
Title:       Ben 10 - Protector of Earth
Game ID:     SLUS_216.61
Version:     1.01
Video mode:  NTSC
Media:       DVD
Size:        3.40 GB

OPL filename:
SLUS_216.61.Ben 10 - Protector of Earth.iso
```

---

## Desenvolvimento

Execute os testes:

```bash
pytest
```

Execute os testes com cobertura:

```bash
pytest --cov=ps2opl
```

Execute o linter:

```bash
ruff check .
```

Corrija automaticamente os problemas suportados pelo linter:

```bash
ruff check . --fix
```

---

## Segurança

Arquivos de jogos nunca devem ser modificados ou sobrescritos sem um comando explícito do usuário.

Operações que renomeiam, movem, removem, dividem ou modificam arquivos devem realizar validações e, quando apropriado, oferecer um modo `dry-run`.

Exemplo:

```bash
ps2opl rename /caminho/para/jogos --dry-run
```

---

## Aviso legal

`ps2opl` é um projeto independente e de código aberto, sem afiliação ou endosso da Sony Interactive Entertainment ou do projeto Open PS2 Loader.

Os usuários são responsáveis pelo cumprimento das leis de direitos autorais aplicáveis e devem utilizar o software apenas com imagens de jogos que estejam legalmente autorizados a utilizar.

---

## Licença

MIT License.

---

