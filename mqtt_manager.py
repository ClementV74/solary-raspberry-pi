import paho.mqtt.client as mqtt
import ssl
import threading
import time

class MQTTManager:
    def __init__(self):
        # Configuration MQTT HiveMQ Cloud
        self.mqtt_server = "713ba7b64fc64ce1b65c6a52ccda09dd.s1.eu.hivemq.cloud"
        self.mqtt_port = 8883
        self.mqtt_user = "solary"
        self.mqtt_pass = "Reseal0-Smokeless9-Peso5-Graceless4-Trustable0"
        
        # Topics pour contrôle des relais
        self.casier1_topic = "borne1/casier1"
        self.casier2_topic = "borne1/casier2"
        
        # Client MQTT
        self.client = mqtt.Client(client_id="solary_borne1", protocol=mqtt.MQTTv311)
        self.client.username_pw_set(self.mqtt_user, self.mqtt_pass)
        
        # Configuration TLS
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.client.tls_set_context(context)
        
        # Callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
        # État de connexion
        self.connected = False
        
        # Démarrer la connexion
        self.start_connection()
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback de connexion MQTT"""
        if rc == 0:
            self.connected = True
            print("✅ Connecté au broker MQTT pour contrôle des relais")
        else:
            self.connected = False
            print(f"❌ Échec de connexion MQTT. Code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback de déconnexion MQTT"""
        self.connected = False
        if rc != 0:
            print("⚠️ Déconnexion MQTT inattendue. Tentative de reconnexion...")
            self.reconnect()
    
    def start_connection(self):
        """Démarre la connexion MQTT dans un thread séparé"""
        def connect_loop():
            while True:
                try:
                    print(f"🔄 Connexion au broker MQTT {self.mqtt_server}:{self.mqtt_port}...")
                    self.client.connect(self.mqtt_server, self.mqtt_port, 60)
                    self.client.loop_forever()
                except Exception as e:
                    print(f"❌ Erreur connexion MQTT: {e}")
                    self.connected = False
                    time.sleep(5)  # Attente avant tentative reconnexion
        self.connection_thread = threading.Thread(target=connect_loop, daemon=True)
        self.connection_thread.start()
    
    def reconnect(self):
        """Tente une reconnexion"""
        if not self.connected:
            try:
                self.client.reconnect()
            except Exception as e:
                print(f"❌ Échec reconnexion: {e}")
                time.sleep(5)
                self.start_connection()
    
    def open_locker(self, casier_id):
        """Ouvre un casier (désactive le relais)"""
        # MQTT doit recevoir "0" pour OUVRIR
        if not self.connected:
            print("⚠️ MQTT non connecté. Simulation ouverture casier.")
            return False

        topic = self.casier1_topic if casier_id == 0 else self.casier2_topic

        try:
            result = self.client.publish(topic, "0", qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"🔓 Commande ouverture envoyée: Casier {casier_id + 1}")
                return True
            else:
                print(f"❌ Échec envoi commande: {result.rc}")
                return False
        except Exception as e:
            print(f"❌ Erreur envoi commande: {e}")
            return False
    
    def close_locker(self, casier_id):
        """Ferme un casier (active le relais)"""
        # MQTT doit recevoir "1" pour FERMER
        if not self.connected:
            print("⚠️ MQTT non connecté. Simulation fermeture casier.")
            return False

        topic = self.casier1_topic if casier_id == 0 else self.casier2_topic

        try:
            result = self.client.publish(topic, "1", qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"🔒 Commande fermeture envoyée: Casier {casier_id + 1}")
                return True
            else:
                print(f"❌ Échec envoi commande: {result.rc}")
                return False
        except Exception as e:
            print(f"❌ Erreur envoi commande: {e}")
            return False
    
    def disconnect(self):
        """Déconnecte proprement du broker MQTT"""
        if self.connected:
            self.client.disconnect()
            self.connected = False
            print("📴 Déconnexion MQTT")
    
    def is_connected(self):
        """Retourne l'état de connexion"""
        return self.connected
