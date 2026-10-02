# Audio Max for Blender 5.0

Audio Max é um addon avançado para o Blender 5.0+ que adiciona processamento profissional de áudio diretamente no Video Sequence Editor (VSE), permitindo converter, exportar e enviar áudio para DAWs externas sem sair do Blender.

---

## ✅ Recursos atuais

- 🔊 **Conversão de áudio do VSE** — extrai o áudio mixado da timeline e exporta em WAV ou MP3
- 🎯 **Detecção automática de canal livre** — o áudio exportado é inserido de volta no VSE no primeiro canal disponível, sem sobrescrever vídeo ou outros strips
- 🎛 **Envio para DAW** — detecta automaticamente DAWs instaladas no sistema e abre o arquivo exportado diretamente nelas
- 🔍 **Detecção automática de DAWs** — suporta Reaper, FL Studio, Ableton, Ardour, Bitwig, Audacity, Carla e outros
- 📂 **Browse manual de DAW** — caso a DAW não seja detectada, é possível selecionar o executável manualmente
- 🧩 **Interface integrada no VSE** — painel lateral acessível via Sidebar (N) → aba AudioMax
- 🔄 **Compatível com Blender 5.0+** — API completamente atualizada (`strips_all`, `bpy.ops.sound.mixdown()`)

---

## 🖥️ Requisitos

- Blender 5.0 ou superior (incluindo versão Steam)
- Windows 10/11 (testado)
- DAW opcional para receber o áudio exportado

---

## 📦 Instalação

1. Baixe o arquivo ZIP do repositório
2. No Blender: **Edit → Preferences → Add-ons → Install**
3. Selecione o ZIP e ative o addon
4. O painel aparecerá no VSE: **Sidebar (N) → aba AudioMax**

---

## 🎚 Como usar

### Converter áudio do VSE
1. Adicione um vídeo (com áudio) na timeline do VSE
2. Abra o painel **AudioMax** no Sidebar
3. Clique em **Convert Audio from VSE**
4. Escolha o formato (WAV ou MP3)
5. O áudio será exportado e adicionado automaticamente ao VSE no primeiro canal livre

### Enviar para DAW
1. Após converter, o addon pergunta se deseja enviar para uma DAW
2. DAWs detectadas automaticamente aparecem como botões
3. Caso sua DAW não apareça, use **Browse for DAW** para selecionar manualmente o executável

---

## 📂 Estrutura do projeto

```
audio_max/
├── __init__.py           # Registro do addon
├── core/
│   ├── audio_export.py   # Exportação de áudio e inserção no VSE
│   └── global_cache.py   # Cache de DAWs detectadas
├── ui/
│   ├── operators.py      # Operadores dos botões
│   └── panels.py         # Painéis da interface
├── external/
│   ├── daw_detector.py   # Detecção automática de DAWs
│   └── host_priority.py  # Ordenação por prioridade de DAW
└── utils/
    ├── paths.py          # Caminhos e diretórios temporários
    ├── logging.py        # Sistema de log interno
    └── system_info.py    # Informações do sistema
```

---

## 🔧 Correções e melhorias — Blender 5.0

| Problema | Correção |
|----------|----------|
| `sequences` / `sequences_all` não existem mais | Migrado para `strips` / `strips_all` |
| `bpy.ops.render.render()` não exporta áudio | Substituído por `bpy.ops.sound.mixdown()` |
| Circular import ao carregar o addon | Lazy import de `audio_export` dentro do `execute()` |
| Import desnecessário de `daw_detector` no `__init__.py` | Removido — detecção ocorre via `global_cache` |
| `AUDIOMAX_PT_MainPanel` nunca aparecia no VSE | Adicionado ao `PANEL_CLASSES` |
| Painel duplicado no SEQUENCE_EDITOR | `AUDIOMAX_PT_Sequencer` removido |
| Ícone `CHECKMARK` inválido no Blender 4.x/5.0 | Substituído por `CHECKBOX_HLT` |
| Áudio exportado não voltava ao VSE | Adicionado `_add_audio_to_vse()` com canal automático |

---

## 🗺️ Roadmap

- [ ] Suporte a FLAC e OGG na interface do painel
- [ ] Equalizador nativo por faixa
- [ ] Monitor de loudness
- [ ] Suporte a macOS e Linux
- [ ] Pré-visualização de efeito ao vivo

---

## 🤝 Contribuindo

Pull Requests são bem-vindos! Antes de enviar:
- Teste no Blender 5.0+
- Descreva claramente o que foi alterado
- Mantenha compatibilidade com Windows

---

## 📜 Licença

Distribuído sob a licença MIT. Você pode usar, modificar e distribuir livremente.

---

## 👤 Autor

Desenvolvido por **Italo Nicacio**.  
Sugestões e issues são bem-vindas no repositório.

---

🎧 *Aproveite o processamento de áudio profissional dentro do Blender!*

## DAW COMPLETA
https://github.com/ItaloNicacioDev/DAW_for_Blender


