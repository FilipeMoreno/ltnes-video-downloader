import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import threading
import shutil
import sys
import requests

# Configuração do auto-update
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/FilipeMoreno/ltnes-video-downloader/refs/heads/main/version.txt"
CHANGELOG_URL = "https://raw.githubusercontent.com/FilipeMoreno/ltnes-video-downloader/main/changelog.txt"
VERSAO_ATUAL = "1.0.4"

# Lista de vídeos a serem baixados
video_list = []
total_videos = 0
current_progress = 0

def verificar_atualizacao():
    try:
        response = requests.get(GITHUB_VERSION_URL, timeout=5)
        response.raise_for_status()
        versao_remota = response.text.strip()

        if versao_remota > VERSAO_ATUAL:
            resposta = messagebox.askyesno("Atualização Disponível", f"Nova versão {versao_remota} disponível!\nDeseja atualizar agora?")
            if resposta:
                baixar_e_instalar_atualizacao(versao_remota)
    except Exception as e:
        print(f"Erro ao verificar atualização: {e}")
        

def baixar_e_instalar_atualizacao(versao):
    try:
        messagebox.showinfo("Baixando", "Baixando a nova versão...")
        novo_arquivo = "update_installer.exe"
        UPDATE_URL = "https://github.com/FilipeMoreno/ltnes-video-downloader/releases/download/" + versao + "/LTNES.Video.Downloader.exe"
        comando = ["curl", "-L", f"{UPDATE_URL}", "-o", novo_arquivo]
        subprocess.run(comando, check=True)

        # Baixa o changelog da nova versão
        changelog = requests.get(CHANGELOG_URL, timeout=5)
        with open("changelog.txt", "w", encoding="utf-8") as f:
            f.write(changelog.text)

        messagebox.showinfo("Instalação", "Iniciando instalação da atualização...")
        subprocess.Popen([novo_arquivo])
        sys.exit()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao atualizar: {e}")

def exibir_changelog():
    if os.path.exists("changelog.txt"):
        with open("changelog.txt", "r", encoding="utf-8") as f:
            changelog = f.read()

        if changelog.strip():
            messagebox.showinfo("Novidades", f"Últimas Atualizações:\n\n{changelog}")

# Função para atualizar a qualidade quando MP3 for selecionado
def update_quality(*args):
    if selected_extension.get() == "mp3":
        selected_quality.set("audio")

# Função para adicionar à lista
def add_to_list():
    url = url_entry.get()
    filename = filename_entry.get()
    output_dir = output_dir_var.get()

    if not url or not filename or not output_dir:
        messagebox.showerror("Erro", "Preencha todos os campos!")
        return

    video_list.append((url, filename))
    url_entry.delete(0, tk.END)
    filename_entry.delete(0, tk.END)
    listbox.insert(tk.END, f"{filename} - {url}")

# Função para selecionar diretório de saída
def select_output_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        output_dir_var.set(folder_selected)

# Função de download do vídeo
def download_video(url, filename, output_dir):
    global current_progress, total_videos

    output_path = os.path.join(output_dir, f"{filename}.%(ext)s")
    extension = selected_extension.get()
    quality = selected_quality.get()

    command = ["yt-dlp", url, "-o", output_path]

    if quality == "audio":
        command.extend(["-f", "bestaudio", "--extract-audio", "--audio-format", extension])
    else:
        command.extend(["-f", f"bestvideo[height={quality}]+bestaudio/best"])

    log_text.insert(tk.END, f"Iniciando: {filename} ({quality}, {extension})\n")
    log_text.see(tk.END)

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

        for line in process.stdout:
            log_text.insert(tk.END, line)
            log_text.see(tk.END)

            if "%" in line:
                try:
                    percent = float(line.split("%")[0].split()[-1])
                    progress_bar["value"] = ((current_progress + percent) / total_videos)
                except:
                    pass

        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)

        current_progress += 100
        progress_bar["value"] = (current_progress / total_videos) * 100

    except subprocess.CalledProcessError:
        log_text.insert(tk.END, f"Erro ao baixar {filename}\n")

# Função para iniciar os downloads
def download_videos():
    global total_videos, current_progress

    if not video_list:
        messagebox.showerror("Erro", "Nenhum vídeo na lista!")
        return

    output_dir = output_dir_var.get()
    log_text.delete(1.0, tk.END)
    progress_bar["value"] = 0
    total_videos = len(video_list)
    current_progress = 0

    threads = []
    for url, filename in video_list:
        thread = threading.Thread(target=download_video, args=(url, filename, output_dir))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    progress_bar["value"] = 100
    messagebox.showinfo("Concluído", "Todos os vídeos foram baixados!")
    video_list.clear()
    listbox.delete(0, tk.END)

# Verificar se yt-dlp está instalado
def check_yt_dlp():
    if shutil.which("yt-dlp"):
        return True

    try:
        subprocess.run(["yt-dlp", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        response = messagebox.askyesno("yt-dlp não encontrado", "Deseja instalar automaticamente com winget?")
        if response:
            try:
                subprocess.run(["winget", "install", "yt-dlp", "--silent"], check=True)
                messagebox.showinfo("Instalação concluída", "yt-dlp instalado!")
                return True
            except subprocess.CalledProcessError:
                messagebox.showerror("Erro", "Falha ao instalar yt-dlp.")
                return False
        return False

# Criar a janela principal
root = tk.Tk()
root.title(f"LTNES Video Downloader - v{VERSAO_ATUAL}") 
root.geometry("700x600")
root.minsize(600, 500)

if not check_yt_dlp():
    messagebox.showerror("Erro", "yt-dlp não encontrado. O programa será encerrado.")
    sys.exit()

verificar_atualizacao()
exibir_changelog()

# Configurar layout responsivo
root.columnconfigure(0, weight=1)

# Variáveis de seleção
selected_quality = tk.StringVar(value="1080p")
selected_extension = tk.StringVar(value="mp4")
selected_extension.trace_add("write", update_quality)

# Frames organizadores
input_frame = ttk.LabelFrame(root, text="Configurações")
input_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

list_frame = ttk.LabelFrame(root, text="Lista de Downloads")
list_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

log_frame = ttk.LabelFrame(root, text="Log")
log_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

quality_frame = ttk.LabelFrame(root, text="Qualidade e Formato")
quality_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

# Entradas de URL e Nome do Arquivo
ttk.Label(input_frame, text="URL do vídeo:").grid(row=0, column=0, sticky="w")
url_entry = ttk.Entry(input_frame, width=60)
url_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="Nome do arquivo:").grid(row=1, column=0, sticky="w")
filename_entry = ttk.Entry(input_frame, width=60)
filename_entry.grid(row=1, column=1, padx=5, pady=5)

# Diretório de saída
output_dir_var = tk.StringVar()
ttk.Label(input_frame, text="Diretório de saída:").grid(row=2, column=0, sticky="w")
ttk.Entry(input_frame, textvariable=output_dir_var, width=50).grid(row=2, column=1, padx=5, pady=5)
ttk.Button(input_frame, text="Selecionar", command=select_output_folder).grid(row=2, column=2, padx=5, pady=5)

# Lista de vídeos com scrollbar
listbox = tk.Listbox(list_frame, width=80, height=10)
scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
listbox.config(yscrollcommand=scrollbar.set)
listbox.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Botões
ttk.Button(list_frame, text="Adicionar", command=add_to_list).pack(side="left", padx=5, pady=5)
ttk.Button(list_frame, text="Baixar Todos", command=lambda: threading.Thread(target=download_videos).start()).pack(side="left", padx=5, pady=5)

# Log com scrollbar
log_text = tk.Text(log_frame, height=10, width=80)
log_text.pack()

# Qualidade e Formato
ttk.Label(quality_frame, text="Qualidade:").grid(row=0, column=0, sticky="w")
quality_combobox = ttk.Combobox(quality_frame, textvariable=selected_quality, values=["1080p", "720p", "480p", "audio"], state="readonly")
quality_combobox.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(quality_frame, text="Formato:").grid(row=1, column=0, sticky="w")
extension_combobox = ttk.Combobox(quality_frame, textvariable=selected_extension, values=["mp4", "mkv", "mp3"], state="readonly")
extension_combobox.grid(row=1, column=1, padx=5, pady=5)

# Barra de progresso
progress_bar = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate")
progress_bar.grid(row=4, column=0, pady=10, sticky="ew")


root.mainloop()
