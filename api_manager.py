"""
Gestionnaire API pour la communication avec le backend Solary
"""

import requests
import json
import threading
import time
from datetime import datetime

class APIManager:
    def __init__(self, base_url=None, api_key=None):
        # Configuration API Solary
        self.base_url = base_url or "https://solary.vabre.ch"
        self.api_key = api_key
        self.borne_id = 1  # ID de cette borne
        
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
        
        # Cache des données API
        self.prises_data = []
        
        print("🔗 APIManager initialisé avec API Solary")
        print(f"   Base URL: {self.base_url}")
        print(f"   Borne ID: {self.borne_id}")
    
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
    
    def get_lockers_status(self):
        """Récupère l'état des casiers depuis l'API Solary"""
        try:
            url = f"{self.base_url}/GetAllPrises"
            print(f"🔄 Appel API: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Données API reçues: {data}")
                
                # Filtrer les prises de cette borne
                borne_prises = [prise for prise in data if prise.get('borne_id') == self.borne_id]
                
                # Trier par prise_id pour avoir l'ordre correct
                borne_prises.sort(key=lambda x: x.get('prise_id', 0))
                
                # Sauvegarder les données complètes
                self.prises_data = borne_prises
                
                # Convertir en format attendu par le système (True = disponible, False = occupé)
                status_list = []
                for prise in borne_prises:
                    is_available = bool(prise.get('is_available', 0))
                    status_list.append(is_available)
                
                print(f"📊 Statuts casiers: {status_list}")
                self.connected = True
                self.last_sync = datetime.now()
                
                return status_list
            else:
                print(f"❌ Erreur API: {response.status_code} - {response.text}")
                self.connected = False
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur réseau API: {e}")
            self.connected = False
            return None
        except Exception as e:
            print(f"❌ Erreur récupération statut API: {e}")
            self.connected = False
            return None
    
    def update_prise_status(self, locker_id, is_available):
        """Met à jour le statut d'une prise via l'API"""
        try:
            # Trouver la prise correspondante
            if locker_id < len(self.prises_data):
                prise = self.prises_data[locker_id]
                prise_id = prise.get('prise_id')
                
                if not prise_id:
                    print(f"❌ Prise ID non trouvé pour casier {locker_id}")
                    return False
                
                url = f"{self.base_url}/UpdatePrise/{prise_id}"
                
                payload = {
                    "id": prise_id,
                    "borne_id": self.borne_id,
                    "is_available": 1 if is_available else 0
                }
                
                print(f"🔄 Mise à jour prise {prise_id}: {payload}")
                
                response = requests.put(url, json=payload, headers=self.headers, timeout=10)
                
                if response.status_code in [200, 204]:
                    print(f"✅ Prise {prise_id} mise à jour avec succès")
                    
                    # Mettre à jour le cache local
                    self.prises_data[locker_id]['is_available'] = 1 if is_available else 0
                    
                    return True
                else:
                    print(f"❌ Erreur mise à jour prise: {response.status_code} - {response.text}")
                    return False
            else:
                print(f"❌ Casier {locker_id} non trouvé dans les données")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur réseau mise à jour: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur mise à jour prise: {e}")
            return False
    
    def reserve_locker(self, locker_id, user_data=None):
        """Réserve un casier (le marque comme occupé)"""
        print(f"🔗 API: Réservation casier {locker_id + 1}")
        return self.update_prise_status(locker_id, False)  # False = occupé
    
    def release_locker(self, locker_id, unlock_code=None):
        """Libère un casier (le marque comme disponible)"""
        print(f"🔗 API: Libération casier {locker_id + 1}")
        return self.update_prise_status(locker_id, True)  # True = disponible
    
    def send_heartbeat(self):
        """Envoie un heartbeat à l'API"""
        try:
            # Pour l'instant, utiliser GetAllPrises comme heartbeat
            result = self.get_lockers_status()
            self.connected = result is not None
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
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur synchronisation: {e}")
            return False
    
    def get_prise_info(self, locker_id):
        """Récupère les informations d'une prise"""
        if locker_id < len(self.prises_data):
            return self.prises_data[locker_id]
        return None
    
    def log_action(self, locker_id, action, details=None):
        """Enregistre une action (pour l'instant juste un log local)"""
        try:
            prise_info = self.get_prise_info(locker_id)
            prise_id = prise_info.get('prise_id') if prise_info else 'unknown'
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "borne_id": self.borne_id,
                "prise_id": prise_id,
                "locker_id": locker_id,
                "action": action,
                "details": details
            }
            
            print(f"📝 API Log: {log_entry}")
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
    
    def get_borne_id(self):
        """Retourne l'ID de la borne"""
        return self.borne_id
    
    def test_connection(self):
        """Test la connexion à l'API"""
        print("🧪 Test de connexion API...")
        result = self.get_lockers_status()
        if result is not None:
            print("✅ Connexion API OK")
            return True
        else:
            print("❌ Connexion API échouée")
            return False
