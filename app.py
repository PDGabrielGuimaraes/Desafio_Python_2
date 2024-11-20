# Bibliotecas padrão
import os
import time
import threading

# Bibliotecas Externas
from pypdf import PdfReader
import pyttsx3
import pygame
import tkinter as tk
from tkinter import filedialog

class PDFPlayer:
    """
    Uma classe para criar um audio player de PDF usando Tkinter.

    Uso esperado:
        root = tk.Tk()
        app = PDFPlayer(root)
        root.mainloop()
    """    

    def __init__(self, root: object):
        
        # Definição dos parâmetros da instância da classe (Equivalente a variáveis globais, mas dentro de uma classe).
        self.max_palavras_linha = 13
        self.pdf_file_path = ""
        self.current_page = 1
        self.number_of_pages = 1
        self.is_dragging_slider = False
        self.music_loaded = False
        self.current_sound = 'results/sound/current.wav'
        self.page_text, self.number_of_pages = self.convert_pdf_to_text(self.current_page, self.pdf_file_path)

        # Por convenção do tkinter, a janela principal é chamada de janela raiz, portanto, root
        self.root = root

        # Inicializadores/construtores do player de áudio e interface gráfica do usuário(GUI) 
        self._InitMixer()
        self._InitGUI()

        #inicia uma nova thread daemon que executa o método position_updater, permitindo que essa operação ocorra em paralelo, sem 'congelar' a aplicação inteira. 
        threading.Thread(target=self.position_updater, daemon=True).start()

    # Funções de uso interno
    def _InitMixer(self):
        """Inicializa o mixer pygame e carrega um arquivo de música."""
        
        pygame.mixer.init()
        pygame.mixer.music.load(os.path.join("results/sound", "pdf.wav"))
        self.convert_text_to_audio(self.page_text)

    def _InitGUI(self):
        """
        Inicializa a interface gráfica do usuário (GUI) para a aplicação.

        Este método configura a janela principal, frames, áreas de texto, barras de rolagem, sliders,
        e botões usados na aplicação. Também configura as propriedades da janela e widgets necessários.

        Widgets são todo tipo de ferramenta do tkinter.
        """

        # Parâmetros da interface gráfica
        self.root.title("mPD player | PD_f player")
        self.root.geometry("")  # fit to content
        self.root.minsize(400, 400)
        self.root.maxsize(700, 700)
        self.root.iconbitmap(default='docs/images/OrangePD_icon2.ico')        

        # Frame para encapsular o Text
        self.text_frame = tk.Frame(self.root, width=600, height=400)
        self.text_frame.pack_propagate(False)  # Impede que o Frame redimensione para caber no conteúdo
        self.text_frame.pack(side=tk.TOP, 
                             padx=10, 
                             pady=10, 
                             expand=True, 
                             fill="both")

        # Barras de rolagem para textos longos
        self.text_scrollbar = tk.Scrollbar(self.text_frame)
        self.text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Parâmetros do texto
        self.text_widget = tk.Text(self.text_frame, 
                                  font=("Arial", 10), 
                                  relief="sunken", 
                                  wrap=tk.WORD, 
                                  yscrollcommand=self.text_scrollbar.set)
        self.text_widget.pack(expand=True, fill="both")
        self.text_scrollbar.config(command=self.text_widget.yview)
        self.text_widget.tag_configure("center", justify='center')
        self.set_screen_text("Select a PDF file.")

        # Parâmetros do 'slider' de áudio
        self.audio_slider = tk.Scale(self.root, 
                                     from_=0, 
                                     to=self.get_audio_length(), 
                                     orient='horizontal', 
                                     length=500, 
                                     sliderlength=20, 
                                     showvalue=0)
        self.audio_slider.pack(pady=5)
        self.audio_slider.bind("<ButtonPress-1>", self.slider_click)
        self.audio_slider.bind("<ButtonRelease-1>", self.slider_release)

        # Frame para encapsular input da página
        lower_frame = tk.Frame(self.root)
        lower_frame.pack(side=tk.LEFT, expand=True, fill="x", pady=(0, 10))

        # Caixa de input de página
        self.page_input = tk.Entry(lower_frame, width=4)
        self.page_input.pack(side=tk.LEFT, anchor="w", padx=(10, 0))
        self.page_input.bind("<Return>", self.navigate_to_page)
        self.page_input.insert(0, f"{self.current_page}")

        # Complemento da caixa de input de pagina, mostrando o total de páginas daquele PDF
        self.page_label = tk.Label(lower_frame, text=f"/{self.number_of_pages}", font=("Arial", 10))
        self.page_label.pack(side=tk.LEFT, anchor="w")

        # Frame para encapsular os botões, está dentro da frame anterior (lower_frame)
        button_frame = tk.Frame(lower_frame)
        button_frame.pack(side=tk.LEFT, anchor="center", expand=True)

        # Botão de voltar página
        button_prev = tk.Button(button_frame, text="Prev", command=self.prev_page)
        button_prev.pack(side=tk.LEFT, padx=3)

        # Botão de toggle de pausar e tocar áudio
        self.button_play_pause = tk.Button(button_frame, text="Play", command=self.play_pause)
        self.button_play_pause.pack(side=tk.LEFT, padx=3)

        # Botão de avançar página
        button_next = tk.Button(button_frame, text="Next", command=self.next_page)
        button_next.pack(side=tk.LEFT, padx=3)

        # Botão de selecionar arquivo PDF
        select_file = tk.Button(lower_frame, text="Select PDF", command=self.browse_file)
        select_file.pack(side=tk.BOTTOM, anchor="e", padx=10)


    # Métodos 'getter'
    def get_is_playing(self):
        return pygame.mixer.music.get_busy()

    def get_paused_pos(self):
        return self.audio_slider.get()

    def get_audio_length(self):
        return pygame.mixer.Sound(self.current_sound).get_length()
    
    def thread_check(self):
        """Checa se as threads foram corretamente inicializados."""

        threads_ativas = threading.enumerate()
        print(f"Total de threads ativas: {len(threads_ativas)}")
        print("Lista de threads:")
        for thread in threads_ativas:
            print(f"- {thread.name} (daemon: {thread.daemon})")


    # Métodos 'Setter'
    def browse_file(self):
        """Opens a file dialog for the user to select a PDF file."""

        # TODO 1: Selecionar manualmente o arquivo PDF a ser lido
        # Dica: filedialog.askopenfilename()
        
        pass # Deletar futuramente        

    def convert_pdf_to_text(self, num_page: int, pdf_file_path: str) -> tuple[str, int]:
        """
        Converte uma página especificada de um arquivo PDF para texto.
        
        Args:
            num_page (int): A página do PDF a ser convertida.
            pdf_file_path (str): O caminho do arquivo PDF.

        Returns:
            tupla: Uma tupla contendo o texto extraído(str) e o número total de páginas (int).
        """

        #TODO 2: Converter PDF em texto 

        #Dica: Experimente usar Try-Exception: Se houver um erro ao ler o arquivo PDF ou se o usuário 
        # sair da caixa de diálogo (via função browse_file) ao buscar um PDF.

        #TODO: return text, self.number_of_pages

        return 'texto da página em lista', self.number_of_pages

    def convert_text_to_audio(self, text: str):
        """
        Converte um texto em um áudio .wav via TTS na pasta 'results/sound/'.
            text (str): O texto a ser convertido em áudio.
        """
        
        #TODO 3: Converter texto da página em um audio .wav no caminho results/sound/current.wav
    
    def play_pause(self):
        """
        Alterna entre play/pause do aúdio.

        É uma única função devido ao botão compartilhado da GUI (Graphic User Interface).
        """

        try:
            # TODO 4: if música não estiver 'loaded': play e atualizar texto do botão
            # TODO: if condição para unpause
            # TODO: if condição para pause
            
            # OBS: Não pode haver conflito entre estados e o botão precisa apresentar o estado correto
            
            pass # Deletar futuramente

        #Este recurso ajuda MUITO, a biblioteca do pygame acusa onde está dando errado no código
        except Exception as e:
            print(f"play music failed: {e}")

    def prev_page(self):
        """Navega para a página anterior."""
        
        # TODO 5: Navega para a página anterior

        # OBS: Não pode navegar para páginas abaixo de 1
        # Dica: utilizar set_new_page

    def next_page(self):
        """Navega para a próxima página."""
                
        # TODO 6: Navega para a próxima página

        # OBS: Não pode navegar para páginas acima de self.number_of_pages
        # Dica: utilizar set_new_page

    def navigate_to_page(self, event=None):
        """Atualiza a pagina atual para a que o usuário digitou."""

        try:
            # TODO 7: Conferir se o input é valido, se está esta entre 1 <= x <= self.number_of_pages
            # TODO: Atualizar a pagina atual para a que o usuário digitou

            pass # Deletar futuramente

        except ValueError:
            print("Invalid input")

    def position_updater(self, val=None):
        """Atualiza a cada 1 segundo a posição do slider de áudio."""

        #TODO 8: Continuamente recebe a posição atual do slider, adiciona 1 segundo e atualiza posição do slider
        #OBS: o áudio só pode atualizar "sozinho" caso o usuário não esteja arrastando o slider, este controle é feito pela variável self.is_dragging_slider


        # \/ Função auxiliar, seu uso não é obrigatório, mas ajuda
        self.thread_check()

    # Eventos de mouse ao interagir com o slider
    def slider_click(self, event=None):
        self.is_dragging_slider = True
        pygame.mixer.music.stop()

    # Eventos de mouse ao interagir com o slider
    def slider_release(self, event=None):
        if self.is_dragging_slider:
            pygame.mixer.music.play(loops=0, start=self.get_paused_pos())
            pygame.mixer.music.set_pos(self.get_paused_pos())
            self.is_dragging_slider = False

    def set_screen_text(self, new_text: list):
        """
        Define o texto da caixa de texto com o da página atual do PDF.
        
        Args:
            new_text (list): O novo texto a ser exibido no rótulo de texto.
        """
        # Adiciona o texto que está em linha na tela e limita a quantidade de palavras máxima por linha
        total_count = 0
        word_counter = 0
        lines = new_text.split()
        for _ in lines:
            word_counter += 1
            if word_counter == self.max_palavras_linha:
                lines.insert(total_count, "\n")
                word_counter = 0
            total_count += 1
        text_content = " ".join(lines)

        # Apaga o texto anterior e adiciona o atual
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, text_content)
        self.text_widget.tag_add("center", "1.0", "end")
        self.text_widget.config(state=tk.DISABLED)

    def set_new_page(self, current_page: int, current_sound: str, pdf_file_path: str):
        """
        Executa todas as conversão do arquivo PDF em texto, áudio e carrega estas alterações na interface.

        Args:
            current_page (int): A página do PDF a ser convertida.
            current_sound (str): O caminho do arquivo de aúdio.
            pdf_file_path (str): O caminho do arquivo PDF.
        """

        # Descarrega o áudio anterior 
        pygame.mixer.music.unload()

        # Converte a página do arquivo PDF em texto e áudio
        new_text, _ = self.convert_pdf_to_text(current_page, pdf_file_path)
        self.convert_text_to_audio(new_text)

        # Carrega o novo arquivo de áudio
        pygame.mixer.music.load(current_sound)

        # Define o texto da tela
        self.set_screen_text(new_text)
        
        # Reseta posição do slider
        self.audio_slider.set(0)
        self.audio_slider.configure(to=self.get_audio_length())
        
        # Garante que o número da pagina na caixa de input esteja correto
        self.page_input.delete(0, tk.END)
        self.page_input.insert(0, f"{current_page}")

        # Inicia 'automaticamente' o áudio
        pygame.mixer.music.play(loops=0, start=0)
        self.button_play_pause.config(text="Pause")


# Condição para executar o código apenas se o iniciar diretamente
if __name__ == "__main__":
    root = tk.Tk()          # Criação da janela 'raiz' pela biblioteca tkinter
    app = PDFPlayer(root)   # Inicialização do nosso objeto PDFPlayer, onde o argumento da nossa classe, é o objeto criado anteriormente
    root.mainloop()         # Função nativa do tkinter que permite a GUI ler e executar funções baseadas em nossos inputs