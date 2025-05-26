
import sys
import subprocess
import importlib.util
import os
import platform

def check_python_version():
    """Vérifie que Python 3.x est utilisé"""
    if sys.version_info[0] < 3:
        print("❌ Python 3 est requis. Vous utilisez Python", sys.version.split()[0])
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} détecté")

def check_module(module_name):
    """Vérifie si un module est installé"""
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        return False
    return True

def install_module(module_name):
    """Installe un module avec pip"""
    print(f"📦 Installation de {module_name}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])

def setup_raspberry_pi():
    """Configuration spécifique pour Raspberry Pi"""
    print("🔧 Configuration pour Raspberry Pi...")
    
    # Vérifier si on est sur Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'Raspberry Pi' not in cpuinfo:
                print("⚠️ Ce script est optimisé pour Raspberry Pi")
                return
    except:
        print("⚠️ Impossible de détecter le type de système")
        return
    
    print("✅ Raspberry Pi détecté")
    
    # Configuration pour écran tactile
    config_lines = [
        "# Configuration écran tactile Solary",
        "hdmi_force_hotplug=1",
        "hdmi_group=2",
        "hdmi_mode=87",
        "hdmi_cvt=480 320 60 6 0 0 0",
        "display_rotate=0"
    ]
    
    config_path = "/boot/config.txt"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                current_config = f.read()
            
            # Vérifier si la configuration est déjà présente
            if "Configuration écran tactile Solary" not in current_config:
                print("📝 Ajout de la configuration écran tactile...")
                with open(config_path, 'a') as f:
                    f.write("\n" + "\n".join(config_lines) + "\n")
                print("✅ Configuration ajoutée. Redémarrage recommandé.")
            else:
                print("✅ Configuration écran tactile déjà présente")
        except PermissionError:
            print("⚠️ Permissions insuffisantes pour modifier /boot/config.txt")
            print("Exécutez avec sudo pour configurer l'écran automatiquement")

def check_and_install_dependencies():
    """Vérifie et installe les dépendances"""
    required_modules = {
        "tkinter": "python3-tk",
        "segno": "segno",
        "PIL": "pillow",
    }
    
    missing_modules = []
    
    for module, pip_name in required_modules.items():
        if not check_module(module):
            if pip_name:
                missing_modules.append((module, pip_name))
    
    if missing_modules:
        print("📦 Installation des dépendances manquantes...")
        
        # Cas spécial pour tkinter sur Raspberry Pi OS
        if any(module == "tkinter" for module, _ in missing_modules):
            print("📦 Installation de tkinter...")
            subprocess.check_call(["sudo", "apt", "update"])
            subprocess.check_call(["sudo", "apt", "install", "-y", "python3-tk"])
        
        # Installer les autres modules
        for module, pip_name in missing_modules:
            if module != "tkinter":
                install_module(pip_name)
    
    print("✅ Toutes les dépendances sont installées")

def generate_qr_code():
    """Génère le QR code pour l'application"""
    print("🔄 Génération du QR code...")
    
    if not os.path.exists("assets"):
        os.makedirs("assets")
    
    default_url = "https://dashboard.vabre.ch/"
    url = input(f"URL pour le QR code (Entrée = {default_url}): ") or default_url
    
    try:
        import segno
        qr = segno.make_qr(url)
        qr_path = "assets/qrcode.png"
        
        # Taille adaptée pour écran 3.5"
        qr.save(qr_path, scale=6, border=2)
        
        print(f"✅ QR code généré: {qr_path}")
        
        with open("assets/qrcode_url.txt", "w") as f:
            f.write(url)
        
        return True
    except Exception as e:
        print(f"❌ Erreur QR code: {e}")
        return False

def create_autostart():
    """Crée un script de démarrage automatique"""
    print("🚀 Configuration du démarrage automatique...")
    
    autostart_dir = os.path.expanduser("~/.config/autostart")
    if not os.path.exists(autostart_dir):
        os.makedirs(autostart_dir)
    
    desktop_file = os.path.join(autostart_dir, "solary.desktop")
    current_dir = os.getcwd()
    
    desktop_content = f"""[Desktop Entry]
Type=Application
Name=Solary
Comment=Système de casiers connectés
Exec=python3 {current_dir}/main.py
Icon={current_dir}/assets/icon.png
Terminal=false
StartupNotify=false
"""
    
    with open(desktop_file, 'w') as f:
        f.write(desktop_content)
    
    print(f"✅ Démarrage automatique configuré: {desktop_file}")

def main():
    """Fonction principale"""
    print("🔍 Configuration Solary pour Raspberry Pi 3.5\"...")
    
    check_python_version()
    setup_raspberry_pi()
    check_and_install_dependencies()
    
    qr_success = generate_qr_code()
    if not qr_success:
        print("⚠️ QR code par défaut sera utilisé")
    
    # Demander si on veut configurer le démarrage automatique
    auto_start = input("Configurer le démarrage automatique ? (o/N): ").lower()
    if auto_start in ['o', 'oui', 'y', 'yes']:
        create_autostart()
    
    print("\n🎉 Configuration terminée!")
    print("💡 Conseils:")
    print("   - Redémarrez le Raspberry Pi si l'écran n'est pas configuré")
    print("   - Utilisez 'python3 main.py' pour lancer l'application")
    print("   - Appuyez sur Échap pour quitter en mode développement")
    
    # Lancer l'application
    launch = input("\nLancer l'application maintenant ? (O/n): ").lower()
    if launch not in ['n', 'non', 'no']:
        print("🚀 Lancement de Solary...")
        subprocess.call([sys.executable, "main.py"])

if __name__ == "__main__":
    main()
