import time
import threading

class LockerManager:
    def __init__(self, mqtt_manager=None, api_manager=None):
        # État local des casiers pour l'affichage (True = libre, False = réservé/occupé)
        self.lockers_display = [False, True]  # Valeurs par défaut
        
        # Codes de déverrouillage fallback
        self.fallback_codes = {
            0: "1234",  # Casier 1
            1: "5678"   # Casier 2
        }
        
        # Gestionnaires
        self.mqtt_manager = mqtt_manager
        self.api_manager = api_manager
        
        # Timers pour auto-fermeture
        self.timers = {}
        
        # Callback pour mise à jour de l'interface
        self.on_status_change_callback = None
        
        print("🎭 LockerManager initialisé")
        
        # Synchroniser avec l'API au démarrage
        if self.api_manager:
            self.sync_with_api()
    
    def set_status_change_callback(self, callback):
        """Définit le callback pour les changements d'état"""
        self.on_status_change_callback = callback
    
    def get_locker_status(self, locker_id):
        """Retourne l'état d'affichage d'un casier (True = libre, False = réservé/occupé)"""
        if 0 <= locker_id < len(self.lockers_display):
            return self.lockers_display[locker_id]
        return False
    
    def get_locker_detailed_status(self, locker_id):
        """Retourne le statut détaillé d'un casier (libre/réservé/occupé)"""
        if self.api_manager:
            return self.api_manager.get_casier_status(locker_id)
        return 'libre'
    
    def reserve_locker(self, locker_id):
        """Réserve un casier (le marque comme réservé)"""
        if 0 <= locker_id < len(self.lockers_display) and self.lockers_display[locker_id]:
            # Mettre à jour localement
            self.lockers_display[locker_id] = False
            print(f"🔒 Casier {locker_id + 1} réservé localement")
            
            # Mettre à jour via l'API
            if self.api_manager:
                success = self.api_manager.reserve_locker(locker_id)
                if success:
                    print(f"✅ Réservation API confirmée pour casier {locker_id + 1}")
                else:
                    print(f"⚠️ Échec réservation API pour casier {locker_id + 1}")
                    # Revenir en arrière si l'API échoue
                    self.lockers_display[locker_id] = True
                    return False
            
            self._notify_status_change()
            return True
        return False
    
    def release_locker(self, locker_id):
        """Libère un casier (le marque comme libre)"""
        if 0 <= locker_id < len(self.lockers_display):
            # Mettre à jour localement
            self.lockers_display[locker_id] = True
            print(f"🔓 Casier {locker_id + 1} libéré localement")
            
            # Mettre à jour via l'API
            if self.api_manager:
                success = self.api_manager.release_locker(locker_id)
                if success:
                    print(f"✅ Libération API confirmée pour casier {locker_id + 1}")
                else:
                    print(f"⚠️ Échec libération API pour casier {locker_id + 1}")
            
            self._notify_status_change()
            return True
        return False
    
    def occupy_locker(self, locker_id):
        """Marque un casier comme occupé (transition réservé -> occupé)"""
        if 0 <= locker_id < len(self.lockers_display):
            print(f"🏠 Casier {locker_id + 1} marqué comme occupé")
            
            # Mettre à jour via l'API
            if self.api_manager:
                success = self.api_manager.occupy_locker(locker_id)
                if success:
                    print(f"✅ Occupation API confirmée pour casier {locker_id + 1}")
                    return True
                else:
                    print(f"⚠️ Échec occupation API pour casier {locker_id + 1}")
                    return False
            
            return True
        return False
    
    def verify_code(self, locker_id, code):
        """Vérifie le code et déclenche l'ouverture physique si correct"""
        if 0 <= locker_id < len(self.lockers_display):
            # Vérifier le statut détaillé du casier
            detailed_status = self.get_locker_detailed_status(locker_id)
            
            if detailed_status == 'reserve':
                # Casier réservé : vérifier le code via l'API
                if self.api_manager:
                    is_valid = self.api_manager.verify_user_code(locker_id, code)
                else:
                    # Fallback sur les codes locaux
                    is_valid = self.fallback_codes.get(locker_id) == code
                    print(f"⚠️ Utilisation du code fallback pour casier {locker_id + 1}")
            elif detailed_status == 'occupe':
                # Casier occupé : utiliser les codes fallback ou API si disponible
                if self.api_manager:
                    is_valid = self.api_manager.verify_user_code(locker_id, code)
                    if not is_valid:
                        # Essayer aussi le code fallback pour la libération
                        is_valid = self.fallback_codes.get(locker_id) == code
                else:
                    is_valid = self.fallback_codes.get(locker_id) == code
            else:
                # Casier libre : ne devrait pas arriver
                print(f"⚠️ Tentative d'ouverture d'un casier libre {locker_id + 1}")
                return False
            
            if is_valid:
                print(f"✅ Code correct pour casier {locker_id + 1}")
                
                # Logger l'action
                if self.api_manager:
                    self.api_manager.log_action(locker_id, "unlock", {"code_used": True, "status": detailed_status})
                
                # Déclencher l'ouverture physique
                self.trigger_physical_opening(locker_id)
                
                # Gérer la transition d'état selon le statut actuel
                if detailed_status == 'reserve':
                    # Réservé -> Occupé
                    self.occupy_locker(locker_id)
                elif detailed_status == 'occupe':
                    # Occupé -> Libre (libération)
                    self.release_locker(locker_id)
                
            else:
                print(f"❌ Code incorrect pour casier {locker_id + 1}")
                
                # Logger la tentative échouée
                if self.api_manager:
                    self.api_manager.log_action(locker_id, "unlock_failed", {"code_used": False, "status": detailed_status})
            
            return is_valid
        return False

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

    def sync_with_api(self):
        """Synchronise l'état avec l'API"""
        if self.api_manager:
            try:
                print("🔄 Synchronisation avec l'API...")
                api_status = self.api_manager.get_lockers_status()
                if api_status:
                    # Mettre à jour l'état local avec les données de l'API
                    self.lockers_display = api_status
                    self._notify_status_change()
                    print(f"✅ État synchronisé avec l'API: {api_status}")
                    return True
                else:
                    print("⚠️ Pas de données API, conservation de l'état local")
                    return False
            except Exception as e:
                print(f"❌ Erreur synchronisation API: {e}")
                return False
        return False
    
    def update_from_api(self, locker_id, status):
        """Met à jour l'état d'un casier depuis l'API"""
        if 0 <= locker_id < len(self.lockers_display):
            self.lockers_display[locker_id] = status
            self._notify_status_change()
            print(f"🔄 API: Casier {locker_id + 1} -> {'LIBRE' if status else 'RÉSERVÉ/OCCUPÉ'}")
    
    def force_sync(self):
        """Force une synchronisation immédiate avec l'API"""
        return self.sync_with_api()
