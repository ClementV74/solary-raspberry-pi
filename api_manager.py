"""
Gestionnaire API pour la communication avec le backend
Prêt pour l'intégration future
"""

import requests
import json
import threading
import time
from datetime import datetime

class APIManager:
    def __init__(self, base_url=None, api_key=None):
        # Configuration API (à définir plus tard)
        self.base_url = base_url or "https://api.solary.example.com"
        self.api_key = api_key
        self.borne_id = "borne1"
        
        # Headers par défaut
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Solary-Borne/1.0"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        
        # État de connexion
        self.connected = False
        self.last_sync = None
        
        # Callbacks
        self.on_status_change_callback = None
        
        # Thread de synchronisation
        self.sync_thread = None
        self.sync_running = False
        
        print("🔗 APIManager initialisé (mode préparation)")
    
    def set_status_change_callback(self, callback):
        """Définit le callback pour les changements d'état"""
        self.on_status_change_callback = callback
    
    def start_sync(self, interval=30):
        """Démarre la synchronisation périodique avec l'API"""
        if not self.sync_running:
            self.sync_running = True
            self.sync_thread = threading.Thread(target=self._sync_loop, args=(interval,), daemon=True)
            self.sync_thread.start()
            print(f"🔄 Synchronisation API démarrée (intervalle: {interval}s)")
    
    def stop_sync(self):
        """Arrête la synchronisation"""
        self.sync_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("⏹️ Synchronisation API arrêtée")
    
    def _sync_loop(self, interval):
        """Boucle de synchronisation"""
        while self.sync_running:
            try:
                self.sync_lockers_status()
                time.sleep(interval)
            except Exception as e:
                print(f"❌ Erreur sync API: {e}")
                time.sleep(interval)
    
    # Méthodes API (à implémenter plus tard)
    
    def get_lockers_status(self):
        """Récupère l'état des casiers depuis l'API"""
        try:
            # TODO: Implémenter l'appel API réel
            # response = requests.get(f"{self.base_url}/bornes/{self.borne_id}/casiers", headers=self.headers)
            # if response.status_code == 200:
            #     data = response.json()
            #     return [casier['available'] for casier in data['casiers']]
            
            # Pour l'instant, retourner None (mode mock)
            return None
            
        except Exception as e:
            print(f"❌ Erreur récupération statut API: {e}")
            return None
    
    def reserve_locker(self, locker_id, user_data=None):
        """Réserve un casier via l'API"""
        try:
            # TODO: Implémenter l'appel API réel
            # payload = {
            #     "casier_id": locker_id,
            #     "action": "reserve",
            #     "timestamp": datetime.now().isoformat(),
            #     "user_data": user_data
            # }
            # response = requests.post(f"{self.base_url}/bornes/{self.borne_id}/casiers/{locker_id}/reserve", 
            #                         json=payload, headers=self.headers)
            # return response.status_code == 200
            
            print(f"🔗 API: Réservation casier {locker_id + 1} (mock)")
            return True
            
        except Exception as e:
            print(f"❌ Erreur réservation API: {e}")
            return False
    
    def release_locker(self, locker_id, unlock_code=None):
        """Libère un casier via l'API"""
        try:
            # TODO: Implémenter l'appel API réel
            # payload = {
            #     "casier_id": locker_id,
            #     "action": "release",
            #     "timestamp": datetime.now().isoformat(),
            #     "unlock_code": unlock_code
            # }
            # response = requests.post(f"{self.base_url}/bornes/{self.borne_id}/casiers/{locker_id}/release", 
            #                         json=payload, headers=self.headers)
            # return response.status_code == 200
            
            print(f"🔗 API: Libération casier {locker_id + 1} (mock)")
            return True
            
        except Exception as e:
            print(f"❌ Erreur libération API: {e}")
            return False
    
    def send_heartbeat(self):
        """Envoie un heartbeat à l'API"""
        try:
            # TODO: Implémenter l'appel API réel
            # payload = {
            #     "borne_id": self.borne_id,
            #     "timestamp": datetime.now().isoformat(),
            #     "status": "online"
            # }
            # response = requests.post(f"{self.base_url}/bornes/{self.borne_id}/heartbeat", 
            #                         json=payload, headers=self.headers)
            # self.connected = response.status_code == 200
            
            self.connected = True  # Mock
            return self.connected
            
        except Exception as e:
            print(f"❌ Erreur heartbeat API: {e}")
            self.connected = False
            return False
    
    def sync_lockers_status(self):
        """Synchronise l'état des casiers"""
        try:
            status = self.get_lockers_status()
            if status and self.on_status_change_callback:
                self.on_status_change_callback(status)
            
            self.last_sync = datetime.now()
            return True
            
        except Exception as e:
            print(f"❌ Erreur synchronisation: {e}")
            return False
    
    def get_unlock_code(self, locker_id, user_token=None):
        """Récupère le code de déverrouillage depuis l'API"""
        try:
            # TODO: Implémenter l'appel API réel
            # response = requests.get(f"{self.base_url}/bornes/{self.borne_id}/casiers/{locker_id}/code", 
            #                        headers=self.headers, params={"token": user_token})
            # if response.status_code == 200:
            #     return response.json().get("code")
            
            # Pour l'instant, retourner None (utiliser les codes locaux)
            return None
            
        except Exception as e:
            print(f"❌ Erreur récupération code API: {e}")
            return None
    
    def log_action(self, locker_id, action, details=None):
        """Enregistre une action dans l'API"""
        try:
            # TODO: Implémenter l'appel API réel
            # payload = {
            #     "borne_id": self.borne_id,
            #     "casier_id": locker_id,
            #     "action": action,
            #     "timestamp": datetime.now().isoformat(),
            #     "details": details
            # }
            # response = requests.post(f"{self.base_url}/logs", json=payload, headers=self.headers)
            # return response.status_code == 200
            
            print(f"📝 API Log: Casier {locker_id + 1} - {action}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur log API: {e}")
            return False
    
    def is_connected(self):
        """Retourne l'état de connexion API"""
        return self.connected
    
    def get_last_sync(self):
        """Retourne la dernière synchronisation"""
        return self.last_sync
