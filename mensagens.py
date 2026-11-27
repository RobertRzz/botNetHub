"""Arquivo central de mensagens e textos do bot.
Edite os textos abaixo livremente mantendo as variáveis entre chaves (ex: {member}, {count}).
"""

BOAS_VINDAS = {
    "entrada_titulo": "👋 Entrou na NETHUB!",
    "entrada_descricao": (
        "Fala {member}, bora fazer grana?\n"
        "Agora somos **{member_count}** membros."
    ),
    "saida_titulo": "👋 Tchau!",
    "saida_descricao": "**{display_name}** (`{username}`) desistiu de ganhar dinheiro.",
}

OPORTUNIDADES = {
    "titulo_prefixo": "📢 ",
    "campo_orcamento": "💰 Orçamento / Modelo",
    "campo_autor": "👤 Publicado por",
    "confirmacao": "Oportunidade publicada em {channel}!",
    "canal_nao_encontrado": "Canal ou fórum `#{channel_name}` não encontrado.",
}

CARGOS = {
    "painel_titulo": "🎭 Escolha seus cargos",
    "painel_descricao": "Clique nos botões abaixo para adicionar ou remover seus cargos de interesse.",
    "adicionado": "✅ Cargo **{role}** adicionado!",
    "removido": "❌ Cargo **{role}** removido.",
}

TICKETS = {
    "painel_titulo": "🎫 Suporte & Validação",
    "painel_descricao": "Selecione abaixo o motivo do seu atendimento para abrir um ticket privado.",
    "fechando": "Gerando transcrição e fechando o ticket...",
}

SEGURANCA = {
    "anti_convite": "{member}, não é permitido enviar convites de outros servidores aqui.",
    "anti_golpe": "🚨 **Anti-Golpe:** {member} teve mensagem removida e recebeu timeout de 10m.",
}
