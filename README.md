# Pop!_OS Hardware Controller

Um utilitário gráfico para monitorar e controlar sua GPU (NVIDIA ou AMD) no Pop!_OS e outras distribuições baseadas em Debian/Ubuntu.

![Screenshot do App]  <!-- Coloque um screenshot aqui depois -->
<img width="376" height="262" alt="Captura de tela de 2025-11-24 05-38-46" src="https://github.com/user-attachments/assets/5c3fa1cb-e24f-49b6-9e63-7b9152d88078" />
<img width="476" height="890" alt="Captura de tela de 2025-11-24 05-38-38" src="https://github.com/user-attachments/assets/dd80ccd4-a131-4dcb-9df2-0387713b70fe" />
<img width="476" height="890" alt="Captura de tela de 2025-11-24 05-38-34" src="https://github.com/user-attachments/assets/75d347a0-37a9-40ff-a9ea-26ac50a79204" />
<img width="476" height="890" alt="Captura de tela de 2025-11-24 05-38-29" src="https://github.com/user-attachments/assets/1de2d345-d881-4bbd-b3d7-a312bfac6348" />

## Funcionalidades

- Monitoramento em tempo real de temperatura, uso de GPU e uso de memória.
- Controle de velocidade da ventoinha.
- Controle de limite de energia (Power Limit).
- Perfis de configuração personalizáveis.
- Tema escuro com interface semitransparente.

## Instalação

1. Baixe o pacote `.deb` da página de Releases.
2. Instale o pacote com o seguinte comando:
   ```bash
   sudo apt install ./v1.0.2.deb
   ```

## Windows (execução)

- **Requisitos**:
  - Python 3 instalado (`python` no PATH)
  - Para NVIDIA: `nvidia-smi` disponível no PATH (normalmente vem com o driver)
  - **AMD no Windows**: ainda não suportado (o projeto usa sysfs do Linux para AMD)

- **Como rodar** (PowerShell):

```powershell
.\run.ps1
```

- **Alternativa** (duplo clique):
  - Execute `run.bat`

## Observações de compatibilidade

- No Windows, o app consegue **monitorar NVIDIA** via `nvidia-smi` (uso/temperatura/memória).
- Funções que dependem de `nvidia-settings`, `sudo`, `pkexec`, `systemd` e `/sys` são específicas de Linux.
- **AMD no Windows (monitoramento)**: para mostrar uso/temperatura/VRAM, instale e execute o **LibreHardwareMonitor** e habilite a exposição de sensores (WMI/CIM).
  - Depois, reabra o app. Se o LibreHardwareMonitor estiver rodando, os campos deixam de aparecer como `N/A`.

## Build (gerar executável)

- **Windows**:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
```

Saída em `dist\INTERFACE-AMD\`.

- **Linux**:

```bash
chmod +x ./build_linux.sh
./build_linux.sh
```

Saída em `dist/interface-amd/`.

## Dados do usuário (config/perfis)

- **Windows**: `%APPDATA%\INTERFACE-AMD\` (config e `profiles.json`)
- **Linux**: `~/.config/INTERFACE-AMD/`
