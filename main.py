import tkinter as tk
from ui import SolaryApp
import subprocess
import re
import signal
import sys

def get_screen_resolution():
    """Détecte automatiquement la résolution de l'écran"""
    try:
        # Essayer d'obtenir la résolution via xrandr
        result = subprocess.run(['xrandr'], capture_output=True, text=True)
        if result.returncode == 0:
            # Chercher la résolution active (marquée avec *)
            lines = result.stdout.split('\n')
            for line in lines:
                if '*' in line and '+' in line:
                    # Extraire la résolution (ex: "480x320")
                    match = re.search(r'(\d+)x(\d+)', line)
                    if match:
                        width, height = int(match.group(1)), int(match.group(2))
                        print(f"Résolution détectée: {width}x{height}")
                        return width, height
    except Exception as e:
        print(f"Erreur lors de la détection de résolution: {e}")
    
    # Résolutions par défaut pour écrans 3.5" courants
    default_resolutions = [
        (480, 320),  # Écran 3.5" horizontal
        (320, 480),  # Écran 3.5" vertical
        (800, 480),  # Écran 7" (au cas où)
    ]
    
    # Tester quelle résolution fonctionne le mieux
    root_test = tk.Tk()
    screen_width = root_test.winfo_screenwidth()
    screen_height = root_test.winfo_screenheight()
    root_test.destroy()
    
    print(f"Résolution système détectée: {screen_width}x{screen_height}")
    
    # Choisir la résolution la plus proche
    for width, height in default_resolutions:
        if abs(screen_width - width) < 100 and abs(screen_height - height) < 100:
            return width, height
    
    # Si rien ne correspond, utiliser la résolution système
    return screen_width, screen_height

def signal_handler(sig, frame):
    """Gestionnaire de signal pour fermeture propre"""
    print("\n🛑 Arrêt demandé, fermeture propre...")
    if 'app' in globals():
        app.on_closing()
    sys.exit(0)

if __name__ == "__main__":
    # Gestionnaire de signaux pour fermeture propre
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Détecter la résolution de l'écran
    screen_width, screen_height = get_screen_resolution()
    
    root = tk.Tk()
    root.title("Solary")
    
    # Configuration pour écran tactile Raspberry Pi
    # Supprimer les décorations de fenêtre
    root.overrideredirect(True)
    
    # Définir la géométrie exacte pour occuper tout l'écran
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    
    # S'assurer que la fenêtre reste au premier plan
    root.attributes('-topmost', True)
    
    # Désactiver le redimensionnement
    root.resizable(False, False)
    
    # Configuration pour écran tactile
    root.configure(cursor="arrow")  # Cacher le curseur sur écran tactile
    
    # Échappement avec la touche Escape (pour le développement)
    root.bind('<Escape>', lambda e: signal_handler(None, None))
    
    # Passer les dimensions à l'application
    app = SolaryApp(root, screen_width, screen_height)
    app.pack(fill=tk.BOTH, expand=True)
    
    # Gestionnaire de fermeture de fenêtre
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    print(f"🚀 Application lancée en {screen_width}x{screen_height}")
    print("💡 Codes de test: Casier 1 = 1234, Casier 2 = 5678")
    print("🎭 Affichage mock: Casier 1 réservé, Casier 2 libre")
    
    root.mainloop()
