import tkinter as tk
import time
from datetime import datetime
import os
from tkinter import PhotoImage
from locker_manager import LockerManager
from mqtt_manager import MQTTManager
from api_manager import APIManager

class SolaryApp(tk.Frame):
    def __init__(self, master=None, screen_width=480, screen_height=320):
        super().__init__(master)
        self.master = master
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Initialiser API Manager (préparé pour le futur)
        self.api_manager = APIManager()
        
        # Initialiser MQTT Manager (juste pour contrôle physique)
        self.mqtt_manager = MQTTManager()
        
        # Initialiser Locker Manager avec MQTT et API
        self.locker_manager = LockerManager(
            mqtt_manager=self.mqtt_manager,
            api_manager=self.api_manager
        )
        
        # Configurer les callbacks
        self.locker_manager.set_status_change_callback(self.on_locker_status_change)
        self.api_manager.set_status_change_callback(self.on_api_status_change)
        
        # Calculer les facteurs d'échelle basés sur la résolution
        self.scale_factor = min(screen_width / 800, screen_height / 600)
        self.is_small_screen = screen_width <= 480 or screen_height <= 320
        
        # Adapter les tailles selon l'écran
        if self.is_small_screen:
            self.base_font_size = 8
            self.title_font_size = 12
            self.header_font_size = 14
            self.button_font_size = 10
            self.keypad_font_size = 12  # Taille réduite pour le clavier tactile
            self.padding = 5
            self.button_padding_x = 15
            self.button_padding_y = 8
        else:
            self.base_font_size = int(12 * self.scale_factor)
            self.title_font_size = int(18 * self.scale_factor)
            self.header_font_size = int(24 * self.scale_factor)
            self.button_font_size = int(14 * self.scale_factor)
            self.keypad_font_size = int(16 * self.scale_factor)
            self.padding = int(10 * self.scale_factor)
            self.button_padding_x = int(20 * self.scale_factor)
            self.button_padding_y = int(10 * self.scale_factor)
        
        # Palette de couleurs moderne
        self.bg_color = "#f8f9fa"
        self.primary_color = "#6c5ce7"
        self.secondary_color = "#a29bfe"
        self.accent_color = "#00cec9"
        self.text_color = "#2d3436"
        self.available_color = "#00b894"
        self.occupied_color = "#e17055"
        self.button_hover = "#5f50e1"
        self.error_color = "#d63031"
        self.success_color = "#00b894"
        self.keypad_color = "#74b9ff"  # Couleur pour les boutons du clavier
        
        # État de l'interface
        self.current_view = "main"
        self.active_locker = None
        self.notification_text = ""
        self.notification_type = "info"
        self.entered_code = ""  # Code saisi via le clavier virtuel
        
        # Charger l'URL du QR code
        self.qr_code_url = self.load_qr_code_url()
        
        self.configure(bg=self.bg_color)
        self.create_widgets()
        self.update_clock()
        
        # Démarrer la synchronisation API automatique
        self.start_api_sync()
        
    def start_api_sync(self):
        """Démarre la synchronisation automatique avec l'API"""
        if self.api_manager:
            # Test de connexion initial
            print("🔄 Test de connexion API initial...")
            self.api_manager.test_connection()
            
            # Synchronisation immédiate
            self.locker_manager.sync_with_api()
            
            # Démarrer la synchronisation périodique (toutes les 15 secondes)
            self.api_manager.start_sync(15)
            print("✅ Synchronisation API automatique activée")
        
    def load_qr_code_url(self):
        """Charge l'URL du QR code depuis le fichier de configuration"""
        try:
            if os.path.exists("assets/qrcode_url.txt"):
                with open("assets/qrcode_url.txt", "r") as f:
                    return f.read().strip()
        except Exception:
            pass
        return "https://dashboard.vabre.ch/"
    
    def on_locker_status_change(self):
        """Callback appelé quand l'état des casiers change"""
        print("🔄 Mise à jour interface suite changement statut casiers")
        if self.current_view == "main":
            self.after(100, self.update_locker_displays)
    
    def on_api_status_change(self, status_list):
        """Callback appelé quand l'API met à jour les statuts"""
        print(f"🔄 Mise à jour depuis API: {status_list}")
        # Mettre à jour le locker manager avec les nouvelles données
        if status_list and len(status_list) >= 2:
            self.locker_manager.lockers_display = status_list
            if self.current_view == "main":
                self.after(100, self.update_locker_displays)
        
    def create_widgets(self):
        # En-tête adapté pour petit écran
        header_height = 60 if self.is_small_screen else 100
        header_frame = tk.Frame(self, bg=self.primary_color, height=header_height)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Logo et titre compacts
        logo_frame = tk.Frame(header_frame, bg=self.primary_color)
        logo_frame.pack(pady=self.padding)
        
        if not self.is_small_screen:
            # Logo seulement sur grands écrans
            logo_canvas = tk.Canvas(logo_frame, width=30, height=30, bg=self.primary_color, highlightthickness=0)
            logo_canvas.create_oval(2, 2, 28, 28, fill=self.accent_color, outline="")
            logo_canvas.create_oval(8, 8, 22, 22, fill=self.primary_color, outline="")
            logo_canvas.pack(side=tk.LEFT, padx=(0, 5))
        
        header_label = tk.Label(
            logo_frame, 
            text="SOLARY", 
            font=("Helvetica", self.header_font_size, "bold"), 
            fg="white", 
            bg=self.primary_color
        )
        header_label.pack(side=tk.LEFT)
        
        if not self.is_small_screen:
            subtitle = tk.Label(
                header_frame, 
                text="Casiers Connectés", 
                font=("Helvetica", self.base_font_size), 
                fg="white", 
                bg=self.primary_color
            )
            subtitle.pack()
        
        # Ajouter indicateurs de connexion
        if not self.is_small_screen:
            status_frame = tk.Frame(header_frame, bg=self.primary_color)
            status_frame.pack(side=tk.RIGHT, padx=10)
            
            # Indicateur MQTT
            mqtt_frame = tk.Frame(status_frame, bg=self.primary_color)
            mqtt_frame.pack(side=tk.RIGHT, padx=5)
            
            self.mqtt_indicator = tk.Canvas(
                mqtt_frame, 
                width=20, 
                height=20, 
                bg=self.primary_color, 
                highlightthickness=0
            )
            self.mqtt_indicator.pack(side=tk.LEFT, padx=(0, 5))
            
            self.mqtt_label = tk.Label(
                mqtt_frame,
                text="MQTT",
                font=("Helvetica", self.base_font_size - 2),
                fg="white",
                bg=self.primary_color
            )
            self.mqtt_label.pack(side=tk.LEFT)
            
            # Indicateur API (préparé pour le futur)
            api_frame = tk.Frame(status_frame, bg=self.primary_color)
            api_frame.pack(side=tk.RIGHT, padx=5)
            
            self.api_indicator = tk.Canvas(
                api_frame, 
                width=20, 
                height=20, 
                bg=self.primary_color, 
                highlightthickness=0
            )
            self.api_indicator.pack(side=tk.LEFT, padx=(0, 5))
            
            self.api_label = tk.Label(
                api_frame,
                text="API",
                font=("Helvetica", self.base_font_size - 2),
                fg="white",
                bg=self.primary_color
            )
            self.api_label.pack(side=tk.LEFT)
            
            # Démarrer la mise à jour des statuts
            self.update_connection_status()
        
        # Conteneur principal avec scroll si nécessaire
        self.main_container = tk.Frame(self, bg=self.bg_color)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=self.padding, pady=self.padding)
        
        # Créer les différentes vues
        self.create_main_view()
        self.create_code_entry_view()
        self.create_notification_view()
        self.create_qr_code_view()
        
        # Afficher la vue principale par défaut
        self.show_view("main")
        
        # Pied de page compact
        if not self.is_small_screen:
            footer_frame = tk.Frame(self, bg=self.primary_color, height=40)
            footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
            footer_frame.pack_propagate(False)
            
            footer_label = tk.Label(
                footer_frame, 
                text="© 2025 Solary", 
                font=("Helvetica", self.base_font_size - 2), 
                fg="white", 
                bg=self.primary_color
            )
            footer_label.pack(pady=10)
    
    def create_main_view(self):
        """Crée la vue principale adaptée pour petit écran"""
        self.main_view = tk.Frame(self.main_container, bg=self.bg_color)
        
        # Horloge compacte
        self.clock_frame = tk.Frame(self.main_view, bg=self.bg_color)
        self.clock_frame.pack(fill=tk.X, pady=(0, self.padding))
        
        self.time_label = tk.Label(
            self.clock_frame, 
            font=("Helvetica", self.base_font_size), 
            bg=self.bg_color, 
            fg=self.text_color
        )
        self.time_label.pack(side=tk.RIGHT)
        
        # Titre compact
        title_label = tk.Label(
            self.main_view, 
            text="Casiers disponibles", 
            font=("Helvetica", self.title_font_size, "bold"), 
            bg=self.bg_color, 
            fg=self.primary_color
        )
        title_label.pack(pady=(0, self.padding))
        
        # Conteneur pour les casiers - layout adaptatif
        lockers_frame = tk.Frame(self.main_view, bg=self.bg_color)
        lockers_frame.pack(fill=tk.BOTH, expand=True)
        
        # Création des casiers avec layout adaptatif
        self.locker_frames = []
        self.locker_status_labels = []
        self.locker_status_texts = []  # Ajouter référence aux textes de statut
        self.locker_buttons = []
        
        # Layout: vertical pour petit écran, horizontal pour grand écran
        layout_vertical = self.is_small_screen
        
        for i in range(2):
            # Frame pour chaque casier
            locker_frame = tk.Frame(
                lockers_frame, 
                bg="white", 
                bd=1, 
                relief=tk.SOLID,
                padx=self.padding, 
                pady=self.padding
            )
            
            if layout_vertical:
                locker_frame.pack(fill=tk.X, pady=self.padding)
            else:
                locker_frame.grid(row=0, column=i, padx=self.padding, pady=self.padding, sticky="nsew")
            
            self.locker_frames.append(locker_frame)
            
            # Layout interne du casier
            if self.is_small_screen:
                # Layout horizontal compact pour petit écran
                info_frame = tk.Frame(locker_frame, bg="white")
                info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                
                button_frame = tk.Frame(locker_frame, bg="white")
                button_frame.pack(side=tk.RIGHT, padx=(self.padding, 0))
            else:
                # Layout vertical pour grand écran
                info_frame = locker_frame
                button_frame = locker_frame
            
            # Titre du casier
            locker_title = tk.Label(
                info_frame, 
                text=f"Casier {i+1}", 
                font=("Helvetica", self.title_font_size, "bold"), 
                bg="white",
                fg=self.primary_color
            )
            locker_title.pack(anchor=tk.W if self.is_small_screen else tk.CENTER)
            
            # État du casier
            locker_status = self.locker_manager.get_locker_status(i)
            
            if self.is_small_screen:
                # Indicateur compact pour petit écran
                status_frame = tk.Frame(info_frame, bg="white")
                status_frame.pack(anchor=tk.W, pady=2)
                
                color = self.available_color if locker_status else self.occupied_color
                status_indicator = tk.Canvas(
                    status_frame, 
                    width=20, 
                    height=20, 
                    bg="white", 
                    highlightthickness=0
                )
                status_indicator.pack(side=tk.LEFT, padx=(0, 5))
                status_indicator.create_oval(2, 2, 18, 18, fill=color, outline="")
                
                status_text = tk.Label(
                    status_frame, 
                    text="DISPONIBLE" if locker_status else "OCCUPÉ", 
                    font=("Helvetica", self.base_font_size, "bold"), 
                    bg="white",
                    fg=color
                )
                status_text.pack(side=tk.LEFT)
                self.locker_status_texts.append(status_text)
            else:
                # Indicateur normal pour grand écran
                status_frame = tk.Frame(info_frame, bg="white")
                status_frame.pack(pady=self.padding)
                
                color = self.available_color if locker_status else self.occupied_color
                status_indicator = tk.Canvas(
                    status_frame, 
                    width=60, 
                    height=60, 
                    bg="white", 
                    highlightthickness=0
                )
                status_indicator.pack()
                status_indicator.create_oval(5, 5, 55, 55, fill=color, outline="")
                status_indicator.create_oval(15, 15, 35, 35, fill="#ffffff", outline="")
                
                status_text = tk.Label(
                    info_frame, 
                    text="DISPONIBLE" if locker_status else "OCCUPÉ", 
                    font=("Helvetica", self.button_font_size, "bold"), 
                    bg="white",
                    fg=color
                )
                status_text.pack()
                self.locker_status_texts.append(status_text)
            
            self.locker_status_labels.append(status_indicator)
            
            # Bouton d'action adapté
            action_button = tk.Button(
                button_frame, 
                text="RÉSERVER" if locker_status else "OUVRIR", 
                font=("Helvetica", self.button_font_size, "bold"), 
                bg=self.primary_color, 
                fg="white",
                activebackground=self.button_hover,
                activeforeground="white",
                bd=0,
                padx=self.button_padding_x, 
                pady=self.button_padding_y,
                cursor="hand2",
                command=lambda idx=i: self.handle_locker_action(idx)
            )
            
            if self.is_small_screen:
                action_button.pack()
            else:
                action_button.pack(pady=self.padding)
            
            self.locker_buttons.append(action_button)
        
        # Configuration du grid pour layout horizontal
        if not layout_vertical:
            lockers_frame.grid_columnconfigure(0, weight=1)
            lockers_frame.grid_columnconfigure(1, weight=1)
    
    def create_code_entry_view(self):
        """Crée la vue de saisie de code avec clavier virtuel tactile"""
        self.code_entry_view = tk.Frame(self.main_container, bg=self.bg_color)
        
        # Conteneur principal centré
        main_frame = tk.Frame(self.code_entry_view, bg="white", padx=self.padding*2, pady=self.padding*2)
        main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Titre adapté
        title_label = tk.Label(
            main_frame,
            text="Code de déverrouillage" if self.is_small_screen else "Entrez votre code de déverrouillage",
            font=("Helvetica", self.title_font_size, "bold"),
            bg="white",
            fg=self.primary_color,
            wraplength=self.screen_width - 40
        )
        title_label.pack(pady=(0, self.padding))
        
        # Sous-titre
        self.code_subtitle = tk.Label(
            main_frame,
            text="Casier X",
            font=("Helvetica", self.button_font_size),
            bg="white",
            fg=self.text_color
        )
        self.code_subtitle.pack(pady=(0, self.padding))
        
        # Affichage du code saisi (remplace l'Entry)
        display_frame = tk.Frame(main_frame, bg="white", bd=2, relief=tk.SOLID)
        display_frame.pack(pady=self.padding)
        
        self.code_display = tk.Label(
            display_frame,
            text="",
            font=("Helvetica", self.title_font_size, "bold"),
            bg="white",
            fg=self.text_color,
            width=8,
            height=1,
            padx=10,
            pady=5
        )
        self.code_display.pack()
        
        # Clavier virtuel numérique
        keypad_frame = tk.Frame(main_frame, bg="white")
        keypad_frame.pack(pady=self.padding)
        
        # Taille des boutons adaptée à l'écran (réduite pour meilleure visibilité)
        if self.is_small_screen:
            button_width = 3
            button_height = 1
            keypad_padx = 1
            keypad_pady = 1
        else:
            button_width = 4
            button_height = 2
            keypad_padx = 3
            keypad_pady = 3
        
        # Création des boutons numériques (disposition 3x3 + 0)
        self.keypad_buttons = []
        
        # Lignes 1-3 (chiffres 1-9)
        for row in range(3):
            row_frame = tk.Frame(keypad_frame, bg="white")
            row_frame.pack(pady=keypad_pady)
            
            for col in range(3):
                number = row * 3 + col + 1
                btn = tk.Button(
                    row_frame,
                    text=str(number),
                    font=("Helvetica", self.keypad_font_size, "bold"),
                    bg=self.keypad_color,
                    fg="white",
                    activebackground=self.button_hover,
                    activeforeground="white",
                    bd=0,
                    width=button_width,
                    height=button_height,
                    cursor="hand2",
                    command=lambda n=number: self.add_digit(str(n))
                )
                btn.pack(side=tk.LEFT, padx=keypad_padx)
                self.keypad_buttons.append(btn)
        
        # Ligne 4 (0 et boutons de contrôle)
        bottom_row = tk.Frame(keypad_frame, bg="white")
        bottom_row.pack(pady=keypad_pady)
        
        # Bouton Effacer
        clear_btn = tk.Button(
            bottom_row,
            text="⌫" if self.is_small_screen else "EFFACER",
            font=("Helvetica", self.keypad_font_size, "bold"),
            bg=self.error_color,
            fg="white",
            activebackground="#b71c1c",
            activeforeground="white",
            bd=0,
            width=button_width,
            height=button_height,
            cursor="hand2",
            command=self.clear_digit
        )
        clear_btn.pack(side=tk.LEFT, padx=keypad_padx)
        
        # Bouton 0
        zero_btn = tk.Button(
            bottom_row,
            text="0",
            font=("Helvetica", self.keypad_font_size, "bold"),
            bg=self.keypad_color,
            fg="white",
            activebackground=self.button_hover,
            activeforeground="white",
            bd=0,
            width=button_width,
            height=button_height,
            cursor="hand2",
            command=lambda: self.add_digit("0")
        )
        zero_btn.pack(side=tk.LEFT, padx=keypad_padx)
        
        # Bouton Valider
        validate_btn = tk.Button(
            bottom_row,
            text="✓" if self.is_small_screen else "OK",
            font=("Helvetica", self.keypad_font_size, "bold"),
            bg=self.success_color,
            fg="white",
            activebackground="#00695c",
            activeforeground="white",
            bd=0,
            width=button_width,
            height=button_height,
            cursor="hand2",
            command=self.validate_code
        )
        validate_btn.pack(side=tk.LEFT, padx=keypad_padx)
        
        # Message d'erreur
        self.code_error = tk.Label(
            main_frame,
            text="Code incorrect",
            font=("Helvetica", self.base_font_size),
            bg="white",
            fg=self.error_color
        )
        
        # Bouton Annuler
        cancel_frame = tk.Frame(main_frame, bg="white")
        cancel_frame.pack(pady=self.padding)
        
        cancel_btn = tk.Button(
            cancel_frame,
            text="Annuler",
            font=("Helvetica", self.button_font_size),
            bg="#dfe6e9",
            fg="#2d3436",
            bd=0,
            padx=self.button_padding_x,
            pady=self.button_padding_y,
            cursor="hand2",
            command=lambda: self.show_view("main")
        )
        cancel_btn.pack()
    
    def add_digit(self, digit):
        """Ajoute un chiffre au code saisi"""
        if len(self.entered_code) < 6:  # Limite à 6 chiffres
            self.entered_code += digit
            self.update_code_display()
            # Cacher le message d'erreur si affiché
            self.code_error.pack_forget()
    
    def clear_digit(self):
        """Efface le dernier chiffre saisi"""
        if self.entered_code:
            self.entered_code = self.entered_code[:-1]
            self.update_code_display()
            # Cacher le message d'erreur si affiché
            self.code_error.pack_forget()
    
    def update_code_display(self):
        """Met à jour l'affichage du code avec des étoiles"""
        display_text = "●" * len(self.entered_code)  # Utiliser des points pour masquer le code
        if not display_text:
            display_text = "Tapez votre code" if self.is_small_screen else "Tapez votre code"
        self.code_display.config(text=display_text)
    
    def create_notification_view(self):
        """Crée la vue de notification adaptée"""
        self.notification_view = tk.Frame(self.main_container, bg=self.bg_color)
        
        center_frame = tk.Frame(self.notification_view, bg="white", padx=self.padding*2, pady=self.padding*2)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Icône adaptée
        icon_size = 60 if self.is_small_screen else 100
        self.notification_icon = tk.Canvas(
            center_frame, 
            width=icon_size, 
            height=icon_size, 
            bg="white", 
            highlightthickness=0
        )
        self.notification_icon.pack(pady=self.padding)
        
        # Texte adapté
        self.notification_label = tk.Label(
            center_frame,
            text="",
            font=("Helvetica", self.title_font_size, "bold"),
            bg="white",
            fg=self.text_color,
            wraplength=self.screen_width - 60,
            justify=tk.CENTER
        )
        self.notification_label.pack(pady=self.padding)
        
        # Bouton de retour
        tk.Button(
            center_frame,
            text="Retour",
            font=("Helvetica", self.button_font_size, "bold"),
            bg=self.primary_color,
            fg="white",
            bd=0,
            padx=self.button_padding_x,
            pady=self.button_padding_y,
            command=lambda: self.show_view("main")
        ).pack(pady=self.padding)
    
    def create_qr_code_view(self):
        """Crée la vue QR code adaptée"""
        self.qr_code_view = tk.Frame(self.main_container, bg=self.bg_color)
        
        center_frame = tk.Frame(self.qr_code_view, bg="white", padx=self.padding*2, pady=self.padding*2)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Titre adapté
        title_text = "App mobile" if self.is_small_screen else "Réservation via l'application mobile"
        title_label = tk.Label(
            center_frame,
            text=title_text,
            font=("Helvetica", self.title_font_size, "bold"),
            bg="white",
            fg=self.primary_color,
            wraplength=self.screen_width - 40
        )
        title_label.pack(pady=(0, self.padding))
        
        if not self.is_small_screen:
            message = tk.Label(
                center_frame,
                text="Scannez le QR code pour réserver",
                font=("Helvetica", self.base_font_size),
                bg="white",
                fg=self.text_color,
                wraplength=self.screen_width - 60
            )
            message.pack(pady=(0, self.padding))
        
        # QR Code adapté
        qr_frame = tk.Frame(center_frame, bg="white")
        qr_frame.pack(pady=self.padding)
        
        self.qr_container = tk.Frame(qr_frame, bg="white")
        self.qr_container.pack()
        
        self.qr_image = None
        self.qr_label = None
        self.load_qr_code()
        
        # URL compacte
        if not self.is_small_screen:
            url_label = tk.Label(
                center_frame,
                text=self.qr_code_url,
                font=("Helvetica", self.base_font_size - 2),
                bg="white",
                fg=self.primary_color
            )
            url_label.pack(pady=self.padding)
        
        # Bouton de retour
        tk.Button(
            center_frame,
            text="Retour",
            font=("Helvetica", self.button_font_size, "bold"),
            bg=self.primary_color,
            fg="white",
            bd=0,
            padx=self.button_padding_x,
            pady=self.button_padding_y,
            command=lambda: self.show_view("main")
        ).pack(pady=self.padding)
    
    def load_qr_code(self):
        """Charge le QR code adapté à la taille d'écran"""
        qr_path = "assets/qrcode.png"
        
        if os.path.exists(qr_path):
            try:
                if self.qr_label:
                    self.qr_label.destroy()
                
                self.qr_image = PhotoImage(file=qr_path)
                
                # Redimensionner si nécessaire pour petit écran
                if self.is_small_screen:
                    # Réduire la taille du QR code pour petit écran
                    self.qr_image = self.qr_image.subsample(2, 2)
                
                self.qr_label = tk.Label(
                    self.qr_container,
                    image=self.qr_image,
                    bg="white"
                )
                self.qr_label.pack()
            except Exception as e:
                print(f"Erreur QR code: {e}")
                self.create_fallback_qr_code()
        else:
            self.create_fallback_qr_code()
    
    def create_fallback_qr_code(self):
        """QR code de secours adapté"""
        if self.qr_label:
            self.qr_label.destroy()
        
        qr_size = 120 if self.is_small_screen else 200
        qr_canvas = tk.Canvas(
            self.qr_container,
            width=qr_size,
            height=qr_size,
            bg="white",
            highlightthickness=1,
            highlightbackground="#e0e0e0"
        )
        qr_canvas.pack()
        
        # QR code simplifié adapté à la taille
        border = 10
        qr_canvas.create_rectangle(border, border, qr_size-border, qr_size-border, fill="white", outline="black", width=2)
        
        # Coins caractéristiques adaptés
        corner_size = qr_size // 6
        
        # Coin supérieur gauche
        qr_canvas.create_rectangle(border*2, border*2, border*2+corner_size, border*2+corner_size, fill="black")
        qr_canvas.create_rectangle(border*2+5, border*2+5, border*2+corner_size-5, border*2+corner_size-5, fill="white")
        
        # Logo central adapté
        center = qr_size // 2
        logo_size = qr_size // 8
        qr_canvas.create_oval(center-logo_size, center-logo_size, center+logo_size, center+logo_size, fill=self.primary_color)
        
        self.qr_label = qr_canvas
    
    def show_view(self, view_name):
        """Affiche la vue spécifiée"""
        self.current_view = view_name
        
        for view in [self.main_view, self.code_entry_view, self.notification_view, self.qr_code_view]:
            view.pack_forget()
        
        if view_name == "main":
            self.main_view.pack(fill=tk.BOTH, expand=True)
            self.update_locker_displays()
        elif view_name == "code_entry":
            self.code_entry_view.pack(fill=tk.BOTH, expand=True)
            self.entered_code = ""  # Réinitialiser le code
            self.update_code_display()
            self.code_error.pack_forget()
        elif view_name == "notification":
            self.notification_view.pack(fill=tk.BOTH, expand=True)
            self.update_notification()
        elif view_name == "qr_code":
            self.qr_code_view.pack(fill=tk.BOTH, expand=True)
    
    def update_clock(self):
        """Met à jour l'horloge"""
        now = datetime.now()
        if self.is_small_screen:
            time_str = now.strftime("%H:%M")
        else:
            date_str = now.strftime("%d %B %Y")
            time_str = now.strftime("%H:%M:%S")
            time_str = f"{date_str} | {time_str}"
        
        self.time_label.config(text=time_str)
        self.after(1000, self.update_clock)
    
    def handle_locker_action(self, locker_id):
        """Gère l'action sur un casier"""
        locker_status = self.locker_manager.get_locker_status(locker_id)
        self.active_locker = locker_id
        
        if locker_status:
            self.show_view("qr_code")
        else:
            self.code_subtitle.config(text=f"Casier {locker_id + 1}")
            self.show_view("code_entry")
    
    def validate_code(self):
        """Valide le code entré via le clavier virtuel"""
        if not self.entered_code:
            return
        
        if self.locker_manager.verify_code(self.active_locker, self.entered_code):
            self.notification_text = f"Casier {self.active_locker + 1} ouvert!\nFermeture automatique dans 20s\nCasier maintenant disponible"
            self.notification_type = "success"
            self.show_view("notification")
            
            # Retour automatique après 4 secondes
            self.after(4000, lambda: self.show_view("main"))
        else:
            self.code_error.pack(pady=(0, self.padding))
            self.entered_code = ""  # Effacer le code incorrect
            self.update_code_display()
    
    def update_notification(self):
        """Met à jour la notification"""
        self.notification_icon.delete("all")
        
        icon_size = 60 if self.is_small_screen else 100
        center = icon_size // 2
        
        if self.notification_type == "success":
            self.notification_icon.create_oval(5, 5, icon_size-5, icon_size-5, fill=self.success_color)
            # Coche adaptée
            self.notification_icon.create_line(center-10, center, center-2, center+8, fill="white", width=3)
            self.notification_icon.create_line(center-2, center+8, center+10, center-8, fill="white", width=3)
            self.notification_label.config(fg=self.success_color)
        elif self.notification_type == "error":
            self.notification_icon.create_oval(5, 5, icon_size-5, icon_size-5, fill=self.error_color)
            # Croix adaptée
            self.notification_icon.create_line(center-8, center-8, center+8, center+8, fill="white", width=3)
            self.notification_icon.create_line(center-8, center+8, center+8, center-8, fill="white", width=3)
            self.notification_label.config(fg=self.error_color)
        else:
            self.notification_icon.create_oval(5, 5, icon_size-5, icon_size-5, fill=self.primary_color)
            font_size = icon_size // 3
            self.notification_icon.create_text(center, center, text="i", fill="white", font=("Helvetica", font_size, "bold"))
            self.notification_label.config(fg=self.primary_color)
        
        self.notification_label.config(text=self.notification_text)
    
    def update_locker_displays(self):
        """Met à jour l'affichage des casiers"""
        print("🔄 Mise à jour affichage de tous les casiers")
        for locker_id in range(2):
            self.update_locker_display(locker_id)
    
    def update_locker_display(self, locker_id):
        """Met à jour l'affichage d'un casier"""
        locker_status = self.locker_manager.get_locker_status(locker_id)
        color = self.available_color if locker_status else self.occupied_color
        status_text = "DISPONIBLE" if locker_status else "OCCUPÉ"
        button_text = "RÉSERVER" if locker_status else "OUVRIR"
        
        print(f"🔄 Mise à jour casier {locker_id + 1}: {status_text}")
        
        # Mettre à jour l'indicateur coloré
        canvas = self.locker_status_labels[locker_id]
        canvas.delete("all")
        
        if self.is_small_screen:
            canvas.create_oval(2, 2, 18, 18, fill=color, outline="")
        else:
            canvas.create_oval(5, 5, 55, 55, fill=color, outline="")
            canvas.create_oval(15, 15, 35, 35, fill="#ffffff", outline="")
        
        # Mettre à jour le texte de statut
        if locker_id < len(self.locker_status_texts):
            self.locker_status_texts[locker_id].config(
                text=status_text,
                fg=color
            )
        
        # Mettre à jour le bouton
        self.locker_buttons[locker_id].config(text=button_text)
    
    def update_connection_status(self):
        """Met à jour les indicateurs de statut de connexion"""
        if hasattr(self, 'mqtt_indicator') and self.mqtt_manager:
            self.mqtt_indicator.delete("all")
            
            if self.mqtt_manager.is_connected():
                # Vert si connecté
                self.mqtt_indicator.create_oval(2, 2, 18, 18, fill="#00b894", outline="")
            else:
                # Rouge si déconnecté
                self.mqtt_indicator.create_oval(2, 2, 18, 18, fill="#e17055", outline="")
        
        if hasattr(self, 'api_indicator') and self.api_manager:
            self.api_indicator.delete("all")
            
            if self.api_manager.is_connected():
                # Vert si connecté
                self.api_indicator.create_oval(2, 2, 18, 18, fill="#00b894", outline="")
            else:
                # Rouge si déconnecté
                self.api_indicator.create_oval(2, 2, 18, 18, fill="#e17055", outline="")
        
        # Répéter toutes les 5 secondes
        self.after(5000, self.update_connection_status)

    def on_closing(self):
        """Méthode appelée à la fermeture de l'application"""
        if self.locker_manager:
            self.locker_manager.cleanup()
        if self.mqtt_manager:
            self.mqtt_manager.disconnect()
        if self.api_manager:
            self.api_manager.stop_sync()
        self.master.destroy()
