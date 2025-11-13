#!/bin/bash

echo "============================================================"
echo "           RELATÓRIO DE CONFIGURAÇÃO DO SHELL (WSL)"
echo "============================================================"
echo

show_file() {
    local FILE="$1"
    if [ -f "$FILE" ]; then
        echo "------------------------------------------------------------"
        echo "📄 Arquivo: $FILE"
        echo "------------------------------------------------------------"
        cat "$FILE"
        echo
    else
        echo "⚠️ Arquivo não encontrado: $FILE"
        echo
    fi
}

echo "======================= HOME FILES ========================="
show_file "$HOME/.bashrc"
show_file "$HOME/.profile"
show_file "$HOME/.bash_profile"

echo "==================== SYSTEM BASH CONFIG ===================="
show_file "/etc/bash.bashrc"
show_file "/etc/profile"

echo "================= /etc/profile.d SCRIPTS ==================="
if [ -d "/etc/profile.d" ]; then
    for f in /etc/profile.d/*.sh; do
        show_file "$f"
    done
else
    echo "⚠️ Diretório /etc/profile.d não encontrado."
fi

echo "==================== ANALISE DE PATH ======================="
echo
echo "➡️ Procurando onde /mnt/c está sendo adicionado ao PATH..."
grep -R "/mnt/c" "$HOME" /etc 2>/dev/null | sed 's/^/  📌 /'
echo
echo "➡️ Procurando alterações do PATH no sistema..."
grep -R "PATH=" "$HOME" /etc 2>/dev/null | sed 's/^/  🔎 /'
echo

echo "============================================================"
echo " Fim do relatório."
echo "============================================================"
