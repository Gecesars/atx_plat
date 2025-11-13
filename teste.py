import google.generativeai as genai
import os
import sys

# Pega a chave da API da variável de ambiente
API_KEY = os.environ.get('GEMINI_API_KEY')

if not API_KEY:
    print("Erro: A variável de ambiente GOOGLE_API_KEY não foi definida.")
    print("Defina a variável antes de rodar o script:")
    print("   export GOOGLE_API_KEY='SUA_CHAVE_AQUI'  (Linux/macOS)")
    print("   set GOOGLE_API_KEY=SUA_CHAVE_AQUI      (Windows CMD)")
    sys.exit(1) # Sai do script se a chave não estiver definida

try:
    # Configura a biblioteca com a sua chave
    genai.configure(api_key=API_KEY)

    # Nota: Usei 'gemini-1.5-flash', que é o modelo Flash mais recente disponível.
    # O modelo 'gemini-2.5-flash' que você mencionou ainda não está publicamente 
    # listado na documentação oficial.
    model = genai.GenerativeModel(model_name='gemini-.5-flash')

    prompt = "Qual é a capital do Brasil?"
    print(f"Enviando prompt: '{prompt}'")
    
    # Envia o prompt para a API
    response = model.generate_content(prompt)

    # Imprime a resposta
    print("\n--- Resposta do Gemini ---")
    print(response.text)
    print("--------------------------")
    print("\nTeste bem-sucedido! Sua chave de API está funcionando.")

except Exception as e:
    print("\n--- Ocorreu um Erro ---")
    print(f"Não foi possível conectar à API. Verifique sua chave ou o erro abaixo:")
    print(e)
    print("-------------------------")