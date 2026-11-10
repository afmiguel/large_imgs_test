import os
import shutil
import subprocess
import time
import urllib.request
from urllib.error import HTTPError, URLError

# Diretórios fornecidos
SRC_DIR = "/Users/afonsomiguel/Downloads/test_thread_download/downloads/large_imgs_test"
DEST_DIR = "/Users/afonsomiguel/Downloads/large_imgs_test"
BASE_URL = "https://afmiguel.github.io/large_imgs_test/"

def get_pending_files():
    """Lista todos os .jpg da origem que ainda não existem no destino."""
    if not os.path.exists(SRC_DIR):
        print(f"Erro: Diretório de origem não encontrado: {SRC_DIR}")
        return []
        
    src_files = sorted([f for f in os.listdir(SRC_DIR) if f.lower().endswith('.jpg')])
    pending = []
    
    for f in src_files:
        if not os.path.exists(os.path.join(DEST_DIR, f)):
            pending.append(f)
            
    return pending

def check_deployment(filename):
    """Fica em loop até o arquivo retornar HTTP 200 no GitHub Pages."""
    # Adiciona um timestamp na URL para evitar que o navegador/provedor guarde o erro 404 em cache
    url = f"{BASE_URL}{filename}?t={int(time.time())}"
    print(f"⏳ Monitorando publicação em: {url}")
    
    while True:
        try:
            # Usamos o método HEAD para verificar se o arquivo existe sem baixar os 25MB
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    print(f"✅ Sucesso! {filename} está online.")
                    break
        except HTTPError as e:
            if e.code == 404:
                print("   Ainda em processamento (404). Aguardando 20 segundos...")
            else:
                print(f"   Erro HTTP {e.code}. Aguardando...")
        except URLError as e:
            print(f"   Falha de rede ({e.reason}). Aguardando...")
            
        time.sleep(20)

def main():
    pending_files = get_pending_files()
    if not pending_files:
        print("Nenhum arquivo pendente para copiar.")
        return

    # Divide a lista de arquivos pendentes em pedaços de 2
    chunks = [pending_files[i:i + 2] for i in range(0, len(pending_files), 2)]
    
    print(f"Total de {len(pending_files)} arquivos pendentes. Divididos em {len(chunks)} lote(s).")
    
    for idx, chunk in enumerate(chunks, 1):
        print(f"\n" + "="*50)
        print(f"🚀 Iniciando Lote {idx}/{len(chunks)}: {', '.join(chunk)}")
        print("="*50)
        
        # 1. Copia os arquivos
        for filename in chunk:
            src_path = os.path.join(SRC_DIR, filename)
            dest_path = os.path.join(DEST_DIR, filename)
            print(f"Copiando: {filename}...")
            shutil.copy2(src_path, dest_path)
            
        # 2. Add, Commit e Push
        try:
            print("Executando Git Push...")
            subprocess.run(["git", "add", "."], cwd=DEST_DIR, check=True, stdout=subprocess.DEVNULL)
            
            commit_msg = f"Upload em lote - Adiciona {', '.join(chunk)}"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=DEST_DIR, check=False, stdout=subprocess.DEVNULL)
            
            subprocess.run(["git", "push"], cwd=DEST_DIR, check=True)
            print("Push concluído com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro durante os comandos do Git: {e}")
            break
            
        # 3. Aguarda o GitHub Pages
        # Basta checar o primeiro arquivo do lote para saber se a esteira toda terminou
        check_deployment(chunk[0])
        
        print(f"Lote {idx} finalizado. Pausa de segurança de 5s antes do próximo lote...")
        time.sleep(5)
        
    print("\n🎉 Todos os lotes foram processados!")

if __name__ == "__main__":
    main()