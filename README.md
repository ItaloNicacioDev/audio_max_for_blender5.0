# audio_max_for_blender5.0
Audio Max é um addon avançado para o Blender 5.0+ que adiciona processamento profissional de áudio diretamente no Video Sequence Editor (VSE), permitindo aplicar efeitos externos via plugins VST, automatizar volumes, organizar trilhas e oferecer ferramentas de mixagem dentro do Blender.

Este projeto foi criado para resolver a limitação nativa do Blender, que não possui suporte interno a VSTs, e expandir suas capacidades de edição de áudio para um nível realmente profissional.

-------------------------------------------------
Recursos principais
-------------------------------------------------
🔊 Aplicação de efeitos VST externos (via FFmpeg ou host externo)
-------------------------------------------------
🎚 Rack de efeitos por faixa
-------------------------------------------------
🎛 Mixer completo com volume, pan e mute
-------------------------------------------------
🎯 Seleção inteligente da faixa de áudio
-------------------------------------------------
🔁 Exportação automática para WAV processado
-------------------------------------------------
⚙️ Suporte para caminhos customizados de VSTs (VST2/VST3)
-------------------------------------------------
🧩 Interface integrada no VSE
-------------------------------------------------
🔄 Compatível com Blender 5.0+ (API atualizada)
---------------------------------------
🖥️ Requisitos

Blender 5.0 ou superior (versão Steam suportada)

FFmpeg instalado e presente no PATH

Plugins VST2 ou VST3 compatíveis

Windows 10/11 (testado)
----------------------------------------

📦 Instalação
1. Baixe o addon

Baixe o arquivo ZIP do repositório:

AudioMax.zip
2. Instale no Blender

Abra Edit → Preferences → Add-ons

Clique em Install

Selecione o ZIP

Ative o addon

3. Configuração inicial

Abra o menu de preferências do addon:

Edit → Preferences → Add-ons → Audio Max

Configure:

Caminho do FFmpeg (se necessário)

Pasta onde ficam seus plugins VST

Pasta temporária para render
-------------------------------------------------
🎚 Usando o plugin no VSE
1. Selecione uma faixa de áudio

Selecione no VSE a faixa que receberá o efeito. Apenas 1 deve estar selecionada.

2. Abra o painel do Audio Max

Localizado no canto direito do VSE:

Sidebar (N) → Aba "Audio Max"
3. Aplique efeitos

No painel você pode:

Adicionar efeitos VST

Editar parâmetros

Processar o áudio

Gerar um novo WAV tratado
---------------------------------------------------
🛠 Comandos internos do Addon
Selecionar faixa de áudio automaticamente

O painel possui um botão:

Selecionar faixa de áudio

Ele detecta a primeira faixa SOUND e seleciona automaticamente.

Processar com VST

Ao clicar em Processar áudio, o addon:

Exporta o strip selecionado para WAV

Envia o arquivo ao host VST configurado

Gera o áudio tratado

Retorna automaticamente para o VSE
-----------------------------------------
📂 Estrutura do Projeto
audio_max/
│
├── __init__.py      # Addon principal
├── ops/              # Operadores
├── ui/               # Painéis, menus e layout
├── utils/            # Funções auxiliares
└── docs/             # Documentação

----------------------------------------
⚠️ Problemas comuns
O Audio Max não aparece no VSE

Certifique-se de que:

Está no Video Sequencer

O painel lateral está aberto (tecla N)

O addon está ativo

O processamento não funciona

Verifique:

FFmpeg instalado

Caminho do VST correto

Permissões de pasta
-----------------------------------------------
🧩 Roadmap

Suporte a múltiplos formatos de áudio

Rack com reorder drag & drop

Monitor de loudness

Equalizador nativo

Pré-visualização de efeito ao vivo

Suporte a macOS e Linux
-------------------------------------------------
🤝 Contribuindo

Pull Requests são bem-vindos!
Antes de enviar, por favor:

Teste no Blender 5.0+

Descreva claramente o que foi alterado

Mantenha compatibilidade com Windows
-------------------------------------------------
📜 Licença

Este projeto é distribuído sob a licença MIT.
Você pode usar, modificar e distribuir livremente.
-------------------------------------------------
👤 Autor

Desenvolvido por Ítalo Nicacio.

Se tiver sugestões, melhorias ou quiser integrar novos efeitos, basta abrir uma Issue.
-------------------------------------------------
🎧 Aproveite o poder dos VSTs dentro do Blender!
