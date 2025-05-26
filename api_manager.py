import requests
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
            "User-Agent": "Solary-Borne/2.0"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        
        # État de connexion
        self.connected = False
        self.last_sync = None
        
        # Callback
        self.on_status_change_callback = None
        
        # Thread de synchronisation
        self.sync_thread = None
        self.sync_running = False
        
        # Cache des données API
        self.casiers_data = []
        
        print("🔗 APIManager initialisé")
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
            url = f"{self.base_url}/GetAllCasiers"
            print(f"🔄 Appel API: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Données API reçues: {data}")
                
                # Filtrer les casiers de cette borne
                borne_casiers = [casier for casier in data if casier.get('borne_id') == self.borne_id]
                
                # Trier par casier_id pour avoir l'ordre correct
                borne_casiers.sort(key=lambda x: x.get('casier_id', 0))
                
                # Sauvegarder les données complètes
                self.casiers_data = borne_casiers
                
                # Convertir en format attendu par le système
                # libre = True (disponible), réservé/occupé = False (non disponible)
                status_list = []
                for casier in borne_casiers:
                    status = casier.get('status', 'libre').lower()
                    is_available = (status == 'libre')
                    status_list.append(is_available)
                
                print(f"📊 Statuts casiers: {[self._get_status_text(s) for s in borne_casiers]}")
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
    
    def _get_status_text(self, casier):
        """Retourne le texte du statut pour le debug"""
        status = casier.get('status', 'libre').lower()
        return f"Casier {casier.get('casier_id', '?')}: {status}"
    
    def get_casier_status(self, locker_id):
        """Récupère le statut détaillé d'un casier spécifique"""
        if locker_id < len(self.casiers_data):
            return self.casiers_data[locker_id].get('status', 'libre').lower()
        return 'libre'
    
    def get_casier_user_id(self, locker_id):
        """Récupère l'user_id associé à un casier"""
        if locker_id < len(self.casiers_data):
            return self.casiers_data[locker_id].get('user_id')
        return None
    
    def get_user_code(self, user_id):
        """Récupère le code d'un utilisateur via l'API GetUser"""
        try:
            url = f"{self.base_url}/GetUser/{user_id}"
            print(f"🔄 Récupération code utilisateur: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                code = user_data.get('code_casiers')
                print(f"✅ Code utilisateur {user_id} récupéré")
                return str(code) if code is not None else None
            else:
                print(f"❌ Erreur récupération utilisateur: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur récupération code utilisateur: {e}")
            return None
    
    def update_status(self, locker_id, new_status):
        """
        Met à jour le statut d'un casier avec gestion intelligente du user_id
        - libre: user_id = null, dates = null
        - reserve: garde user_id existant
        - occupe: user_id = null (sécurité)
        """
        try:
            # Trouver le casier correspondant
            if locker_id < len(self.casiers_data):
                casier = self.casiers_data[locker_id]
                casier_id = casier.get('casier_id')
                
                if not casier_id:
                    print(f"❌ Casier ID non trouvé pour casier {locker_id}")
                    return False
                
                # URL pour la mise à jour
                url = f"{self.base_url}/UpdateCasier/{casier_id}"
                
                # Gestion intelligente selon le statut
                if new_status.lower() == 'libre':
                    # Alternative: ne pas envoyer user_id quand on veut null
                    payload = {
                        "borne_id": casier.get('borne_id', self.borne_id),
                        "status": new_status,
                        "date_reservation": None,
                        "date_occupation": None
                    }
                    # Ne pas inclure user_id du tout
                    print(f"🔄 Libération complète casier {casier_id}: user_id omis")
                    
                elif new_status.lower() == 'occupe':
                    # Occupé: user_id à 0 pour sécurité
                    payload = {
                        "borne_id": casier.get('borne_id', self.borne_id),
                        "user_id": "",  # Essayer 0 au lieu de None
                        "status": new_status,
                        "date_reservation": casier.get('date_reservation'),
                        "date_occupation": datetime.now().isoformat()
                    }
                    print(f"🔄 Occupation casier {casier_id}: user_id → 0 (sécurité)")
                    
                elif new_status.lower() == 'reserve':
                    # Réservé: garde user_id existant (mais pas None)
                    current_user_id = casier.get('user_id')
                    if current_user_id is None:
                        current_user_id = ""  # Fallback si None
                    
                    payload = {
                        "borne_id": casier.get('borne_id', self.borne_id),
                        "user_id": current_user_id,
                        "status": new_status,
                        "date_reservation": casier.get('date_reservation'),
                        "date_occupation": casier.get('date_occupation')
                    }
                    print(f"🔄 Réservation casier {casier_id}: user_id = {current_user_id}")
                    
                else:
                    # Statut inconnu: garde tout tel quel (mais pas None pour user_id)
                    current_user_id = casier.get('user_id')
                    if current_user_id is None:
                        current_user_id = ""  # Fallback si None
                        
                    payload = {
                        "borne_id": casier.get('borne_id', self.borne_id),
                        "user_id": current_user_id,
                        "status": new_status,
                        "date_reservation": casier.get('date_reservation'),
                        "date_occupation": casier.get('date_occupation')
                    }
                    print(f"🔄 Mise à jour casier {casier_id}: {new_status}")
                
                print(f"📤 Payload: {payload}")
                
                response = requests.put(url, json=payload, headers=self.headers, timeout=10)
                
                if response.status_code in [200, 204]:
                    print(f"✅ Casier {casier_id} mis à jour avec succès")
                    
                    # Mettre à jour le cache local
                    self.casiers_data[locker_id]['status'] = new_status
                    if new_status.lower() in ['libre', 'occupe']:
                        self.casiers_data[locker_id]['user_id'] = ""  # 0 au lieu de None
                    if new_status.lower() == 'libre':
                        self.casiers_data[locker_id]['date_reservation'] = None
                        self.casiers_data[locker_id]['date_occupation'] = None
                    
                    return True
                else:
                    print(f"❌ Erreur mise à jour casier: {response.status_code} - {response.text}")
                    return False
            else:
                print(f"❌ Casier {locker_id} non trouvé dans les données")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur réseau mise à jour: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur mise à jour casier: {e}")
            return False
    
    def update_casier_status(self, locker_id, new_status):
        """Ancienne méthode - utilise maintenant update_status"""
        return self.update_status(locker_id, new_status)
    
    def reserve_locker(self, locker_id, user_data=None):
        """Réserve un casier (le marque comme réservé)"""
        print(f"🔗 API: Réservation casier {locker_id + 1}")
        return self.update_status(locker_id, "reserve")
    
    def occupy_locker(self, locker_id):
        """Marque un casier comme occupé (user_id → null pour sécurité)"""
        print(f"🔗 API: Occupation casier {locker_id + 1}")
        return self.update_status(locker_id, "occupe")
    
    def release_locker(self, locker_id, unlock_code=None):
        """Libère un casier (le marque comme libre, user_id → null)"""
        print(f"🔗 API: Libération casier {locker_id + 1}")
        return self.update_status(locker_id, "libre")
    
    def verify_user_code(self, locker_id, entered_code):
        """Vérifie le code d'un utilisateur pour un casier réservé"""
        try:
            # Récupérer l'user_id du casier
            user_id = self.get_casier_user_id(locker_id)
            if not user_id:
                print(f"❌ Aucun utilisateur associé au casier {locker_id + 1}")
                return False
            
            # Récupérer le code de l'utilisateur
            expected_code = self.get_user_code(user_id)
            if not expected_code:
                print(f"❌ Impossible de récupérer le code pour l'utilisateur {user_id}")
                return False
            
            # Comparer les codes
            is_valid = str(entered_code) == str(expected_code)
            print(f"🔐 Vérification code casier {locker_id + 1}: {'✅ Valide' if is_valid else '❌ Invalide'}")
            
            return is_valid
            
        except Exception as e:
            print(f"❌ Erreur vérification code: {e}")
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
    
    def get_casier_info(self, locker_id):
        """Récupère les informations d'un casier"""
        if locker_id < len(self.casiers_data):
            return self.casiers_data[locker_id]
        return None
    
    def log_action(self, locker_id, action, details=None):
        """Enregistre une action (log local)"""
        try:
            casier_info = self.get_casier_info(locker_id)
            casier_id = casier_info.get('casier_id') if casier_info else 'unknown'
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "borne_id": self.borne_id,
                "casier_id": casier_id,
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
