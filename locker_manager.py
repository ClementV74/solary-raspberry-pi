import time
import json
import os
import threading

class LockerManager:
    def __init__(self, mqtt_manager=None, api_manager=None):
        # État mock des casiers pour l'affichage (True = libre, False = réservé)
        self.lockers_display = [False, True]  # Casier 1 réservé, Casier 2 libre (mock)
        
        # Codes de déverrouillage
        self.unlock_codes = {
            0: "1234",  # Casier 1
            1: "5678"   # Casier 2
        }
        
        # Gestionnaire MQTT pour contrôle physique
        self.mqtt_manager = mqtt_manager
        
        # Gestionnaire API pour la logique métier (futur)
        self.api_manager = api_manager
        
        # Timers pour auto-fermeture
        self.timers = {}
        
        # Callbacks pour mise à jour de l'interface
        self.on_status_change_callback = None
        
        print("🎭 LockerManager initialisé avec données mock")
        print(f"   Casier 1: {'LIBRE' if self.lockers_display[0] else 'RÉSERVÉ'}")
        print(f"   Casier 2: {'LIBRE' if self.lockers_display[1] else 'RÉSERVÉ'}")
    
    def set_status_change_callback(self, callback):
        """Définit le callback pour les changements d'état"""
        self.on_status_change_callback = callback
    
    def get_locker_status(self, locker_id):
        """Retourne l'état d'affichage d'un casier (True = libre, False = réservé)"""
        if 0 <= locker_id < len(self.lockers_display):
            return self.lockers_display[locker_id]
        return False
    
    def reserve_locker(self, locker_id):
        """Réserve un casier (le marque comme occupé) - Mock pour l'instant"""
        if 0 <= locker_id < len(self.lockers_display) and self.lockers_display[locker_id]:
            self.lockers_display[locker_id] = False
            print(f"🎭 Mock: Casier {locker_id + 1} réservé")
            self._notify_status_change()
            return True
        return False
    
    def release_locker(self, locker_id):
        """Libère un casier (le marque comme disponible) - Mock pour l'instant"""
        if 0 <= locker_id < len(self.lockers_display):
            self.lockers_display[locker_id] = True
            print(f"🎭 Mock: Casier {locker_id + 1} libéré")
            self._notify_status_change()
            return True
        return False
    
    def verify_code(self, locker_id, code):
        """Vérifie le code et déclenche l'ouverture physique si correct"""
        if 0 <= locker_id < len(self.lockers_display):
            is_valid = self.unlock_codes.get(locker_id) == code
            
            if is_valid:
                print(f"✅ Code correct pour casier {locker_id + 1}")
                
                # Déclencher l'ouverture physique
                self.trigger_physical_opening(locker_id)
                
                # Libérer le casier en mock (il devient disponible)
                self.release_locker(locker_id)
                
                # TODO: Appeler l'API pour marquer le casier comme libéré
                if self.api_manager:
                    self.api_manager.release_locker(locker_id)
                
            else:
                print(f"❌ Code incorrect pour casier {locker_id + 1}")
            
            return is_valid
        return False
    
    def handle_mqtt_command(self, casier_id, command):
        """Traite une commande MQTT (1 = ouvrir, 0 = fermer)"""
        # Pour l'instant, juste pour le contrôle physique
        pass
    
    def set_unlock_code(self, locker_id, code):
        """Définit le code de déverrouillage d'un casier"""
        if 0 <= locker_id < len(self.lockers_display):
            self.unlock_codes[locker_id] = code
            print(f"🔑 Code modifié pour casier {locker_id + 1}: {code}")
            return True
        return False
    
    def save_state(self):
        """Sauvegarde l'état des casiers dans un fichier"""
        try:
            state = {
                "lockers_display": self.lockers_display,
                "unlock_codes": self.unlock_codes,
                "last_update": time.time()
            }
            
            if not os.path.exists("data"):
                os.makedirs("data")
            
            with open("data/locker_state.json", "w") as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            print(f"Erreur sauvegarde état: {e}")
    
    def load_state(self):
        """Charge l'état des casiers depuis un fichier"""
        try:
            if os.path.exists("data/locker_state.json"):
                with open("data/locker_state.json", "r") as f:
                    state = json.load(f)
                
                self.lockers_display = state.get("lockers_display", [False, True])
                self.unlock_codes = state.get("unlock_codes", {0: "1234", 1: "5678"})
                
                # Convertir les clés string en int si nécessaire
                if isinstance(list(self.unlock_codes.keys())[0], str):
                    self.unlock_codes = {int(k): v for k, v in self.unlock_codes.items()}
                
                print("État des casiers chargé depuis le fichier")
                
        except Exception as e:
            print(f"Erreur chargement état: {e}")
            # Utiliser les valeurs par défaut
            self.lockers_display = [False, True]
            self.unlock_codes = {0: "1234", 1: "5678"}

    def trigger_physical_opening(self, locker_id):
        """Déclenche l'ouverture physique du casier avec timer de 20 secondes"""
        print(f"🔓 Déclenchement ouverture physique casier {locker_id + 1}")
        
        # Annuler le timer précédent s'il existe
        if locker_id in self.timers:
            self.timers[locker_id].cancel()
        
        # Envoyer commande d'ouverture via MQTT
        if self.mqtt_manager:
            self.mqtt_manager.open_locker(locker_id)
        
        # Programmer la fermeture automatique après 20 secondes
        def auto_close():
            print(f"⏰ Auto-fermeture casier {locker_id + 1} après 20 secondes")
            if self.mqtt_manager:
                self.mqtt_manager.close_locker(locker_id)
        
        self.timers[locker_id] = threading.Timer(20.0, auto_close)
        self.timers[locker_id].start()
        
        print(f"⏱️ Timer de 20 secondes activé pour casier {locker_id + 1}")
    
    def toggle_mock_status(self, locker_id):
        """Bascule l'état mock d'un casier (pour tests)"""
        if 0 <= locker_id < len(self.lockers_display):
            self.lockers_display[locker_id] = not self.lockers_display[locker_id]
            status = "LIBRE" if self.lockers_display[locker_id] else "RÉSERVÉ"
            print(f"🎭 Mock casier {locker_id + 1} -> {status}")
            self._notify_status_change()
            return True
        return False
    
    def _notify_status_change(self):
        """Notifie l'interface d'un changement d'état"""
        if self.on_status_change_callback:
            self.on_status_change_callback()
    
    def cleanup(self):
        """Nettoie les timers actifs"""
        for timer in self.timers.values():
            if timer.is_alive():
                timer.cancel()
        self.timers.clear()
        print("🧹 Timers nettoyés")

    # Méthodes pour future intégration API
    def sync_with_api(self):
        """Synchronise l'état avec l'API (futur)"""
        if self.api_manager:
            try:
                # TODO: Récupérer l'état depuis l'API
                api_status = self.api_manager.get_lockers_status()
                if api_status:
                    self.lockers_display = api_status
                    self._notify_status_change()
                    print("🔄 État synchronisé avec l'API")
            except Exception as e:
                print(f"❌ Erreur synchronisation API: {e}")
    
    def update_from_api(self, locker_id, status):
        """Met à jour l'état d'un casier depuis l'API (futur)"""
        if 0 <= locker_id < len(self.lockers_display):
            self.lockers_display[locker_id] = status
            self._notify_status_change()
            print(f"🔄 API: Casier {locker_id + 1} -> {'LIBRE' if status else 'RÉSERVÉ'}")
