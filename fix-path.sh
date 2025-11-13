#!/bin/bash

echo "🔧 Corrigindo PATH corrompido..."

TARGET="/home/atx/.profile"

if [ ! -f "$TARGET" ]; then
    echo "❌ Arquivo não encontrado: $TARGET"
    exit 1
fi

echo "📄 Backup criado: $TARGET.bak"
cp "$TARGET" "$TARGET.bak"

# Remove aspas sobrando e linhas duplicadas.
sed -i \
    -e 's|"||g' \
    -e 's|PATH=\$HOME/bin:\$PATH||g' \
    -e 's|PATH=\$HOME/.local/bin:\$PATH||g' \
    "$TARGET"

# Adiciona PATH correto e seguro
cat << 'EOF' >> "$TARGET"

### --- PATH FIXED BY GPT ---
# Garante PATH limpo
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/bin:$PATH"
### --- END FIX ---
EOF

echo "✅ PATH corrigido."
echo "Reinicie o WSL com:"
echo "  wsl --shutdown"
