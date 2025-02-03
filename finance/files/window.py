import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import threading

# Definir diretório absoluto do extract_bank/
DIRETORIO_IMPORTACAO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "extract_bank"))

# Criar diretório se não existir
os.makedirs(DIRETORIO_IMPORTACAO, exist_ok=True)

# Caminho correto do analiser.py
CAMINHO_ANALISER = os.path.abspath(os.path.join(os.path.dirname(__file__), "analiser.py"))

# Caminho para o script de gráfico do Streamlit
CAMINHO_VIEWGRAPH = os.path.abspath(os.path.join(os.path.dirname(__file__), "viewgraph.py"))

class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Carregar Dados Financeiros")
        self.root.geometry("600x500")

        # Inicializa o controle do processo do Streamlit
        self.streamlit_process = None

        # --- Frame principal ---
        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(main_frame)
        self.scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # --- Botões ---
        frame_top = tk.Frame(self.scrollable_frame)
        frame_top.pack(pady=10)

        tk.Button(frame_top, text="Selecionar Arquivos", command=self.selecionar_arquivos).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_top, text="Deletar Arquivos", command=self.deletar_arquivos).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_top, text="Selecionar Todos", command=self.selecionar_todos_arquivos).pack(side=tk.LEFT, padx=5)

        # --- Lista de Arquivos ---
        self.frame_lista = tk.LabelFrame(self.scrollable_frame, text="Arquivos Carregados", padx=10, pady=10)
        self.frame_lista.pack(fill="both", expand=True, padx=10, pady=5)

        self.lista_arquivos = []
        self.check_vars = []
        self.listar_arquivos()

        # --- Botão Analisar ---
        tk.Button(self.scrollable_frame, text="Analisar", command=self.analisar_selecionados).pack(pady=5)

        # --- Log de Processamento ---
        self.frame_log = tk.LabelFrame(self.scrollable_frame, text="Log de Carregamento", padx=10, pady=10)
        self.frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(self.frame_log, height=8)
        self.log_text.pack(fill="both", expand=True)

        # --- Botão Abrir Gráfico ---
        tk.Button(self.scrollable_frame, text="Abrir Gráfico", command=self.abrir_grafico).pack(pady=10)

    def selecionar_arquivos(self):
        arquivos = filedialog.askopenfilenames(filetypes=[("Arquivos OFX", "*.ofx")])
        if not arquivos:
            return

        for arquivo in arquivos:
            nome_arquivo = os.path.basename(arquivo)
            destino = os.path.join(DIRETORIO_IMPORTACAO, nome_arquivo)

            try:
                shutil.copy(arquivo, destino)
                self.log_text.insert(tk.END, f"✅ Arquivo importado: {nome_arquivo}\n")
            except Exception as e:
                self.log_text.insert(tk.END, f"❌ Erro ao importar {nome_arquivo}: {str(e)}\n")

        self.listar_arquivos()

    def deletar_arquivos(self):
        arquivos_selecionados = [arquivo for var, arquivo in self.check_vars if var.get()]
        if not arquivos_selecionados:
            messagebox.showwarning("Nenhum Arquivo", "Selecione ao menos um arquivo para deletar.")
            return

        for arquivo in arquivos_selecionados:
            caminho_arquivo = os.path.join(DIRETORIO_IMPORTACAO, arquivo)
            try:
                os.remove(caminho_arquivo)
                self.log_text.insert(tk.END, f"🗑️ Arquivo deletado: {arquivo}\n")
            except Exception as e:
                self.log_text.insert(tk.END, f"❌ Erro ao deletar {arquivo}: {str(e)}\n")

        self.listar_arquivos()

    def listar_arquivos(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        self.lista_arquivos = os.listdir(DIRETORIO_IMPORTACAO)
        self.check_vars = []

        if not self.lista_arquivos:
            tk.Label(self.frame_lista, text="Nenhum arquivo carregado.").pack()
            return

        for arquivo in self.lista_arquivos:
            var = tk.BooleanVar()
            check = tk.Checkbutton(self.frame_lista, text=arquivo, variable=var)
            check.pack(anchor="w")
            self.check_vars.append((var, arquivo))

    def selecionar_todos_arquivos(self):
        for var, _ in self.check_vars:
            var.set(True)  # Marca todos os arquivos como selecionados

    def analisar_selecionados(self):
        selecionados = [arquivo for var, arquivo in self.check_vars if var.get()]
        
        if not selecionados:
            messagebox.showwarning("Nenhum Arquivo", "Selecione ao menos um arquivo para análise.")
            return

        self.log_text.insert(tk.END, "🔍 Iniciando análise...\n")
        self.log_text.update()  # Força a atualização do log na tela antes de iniciar o processo

        # Rodar a análise em uma thread separada para não bloquear a GUI
        threading.Thread(target=self.executar_analise, args=(selecionados,)).start()

    def executar_analise(self, selecionados):
        try:
            # Captura a saída do analiser.py e exibe no log em tempo real
            process = subprocess.Popen(
                ["python3", CAMINHO_ANALISER, *selecionados], 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Chama a função de leitura em tempo real da saída do processo
            self.read_output(process)

        except subprocess.CalledProcessError as e:
            self.atualizar_log(f"❌ Erro ao rodar análise: {e}\n")

    def read_output(self, process):
        while True:
            stdout_line = process.stdout.readline()
            stderr_line = process.stderr.readline()
            
            if stdout_line:
                self.atualizar_log(stdout_line)
            if stderr_line:
                self.atualizar_log(stderr_line)

            # Se o processo acabou e não há mais saída, paramos de ler
            if stdout_line == '' and stderr_line == '' and process.poll() is not None:
                break

            # Continuar lendo a saída em pequenos intervalos
            self.root.after(100, self.read_output, process)

    def atualizar_log(self, mensagem):
        # Função para atualizar a área de log de forma thread-safe
        self.log_text.after(0, self.log_text.insert, tk.END, mensagem)
        self.log_text.after(0, self.log_text.yview, tk.END)
        self.log_text.after(0, self.log_text.update_idletasks)  # Atualiza a interface gráfica

    def abrir_grafico(self):
        # Verifica se o processo do Streamlit já está em execução
        if self.streamlit_process is not None and self.streamlit_process.poll() is None:
            self.log_text.insert(tk.END, "⚠️ O gráfico já está sendo exibido. Encerrando e reiniciando...\n")
            self.streamlit_process.terminate()  # Finaliza o processo existente

        # Rodar o comando do Streamlit em uma nova thread
        threading.Thread(target=self.executar_streamlit).start()

    def executar_streamlit(self):
        try:
            # Executa o comando do Streamlit para abrir o gráfico
            self.streamlit_process = subprocess.Popen(["streamlit", "run", CAMINHO_VIEWGRAPH])
        except Exception as e:
            self.log_text.insert(tk.END, f"❌ Erro ao abrir o gráfico: {str(e)}\n")

# Criar janela principal
root = tk.Tk()
app = FinanceApp(root)
root.mainloop()
