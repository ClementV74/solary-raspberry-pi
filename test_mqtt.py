#!/usr/bin/env python3
"""
Script de test pour la connexion MQTT
"""

import time
import json
from mqtt_manager import MQTTManager

def test_mqtt_connection():
    """Test de base de la connexion MQTT"""
    print("🧪 Test de connexion MQTT...")
    
    def on_test_message(casier_id, command):
        print(f"📨 Message de test reçu: Casier {casier_id + 1}, Commande: {command}")
    
    # Créer le gestionnaire MQTT
    mqtt_manager = MQTTManager(on_message_callback=on_test_message)
    
    # Attendre la connexion
    print("⏳ Attente de la connexion...")
    timeout = 30
    start_time = time.time()
    
    while not mqtt_manager.is_connected() and (time.time() - start_time) < timeout:
        time.sleep(1)
        print(".", end="", flush=True)
    
    print()
    
    if mqtt_manager.is_connected():
        print("✅ Connexion MQTT réussie!")
        
        # Test de publication
        print("📤 Test de publication...")
        mqtt_manager.publish_locker_action(0, "test", "1234")
        mqtt_manager.publish_locker_status([True, False])
        
        # Attendre les messages
        print("⏳ Écoute des messages pendant 30 secondes...")
        print("💡 Envoyez des messages sur les topics:")
        print("   - borne1/casier1 (payload: 0 ou 1)")
        print("   - borne1/casier2 (payload: 0 ou 1)")
        
        time.sleep(30)
        
        # Déconnexion
        mqtt_manager.disconnect()
        print("✅ Test terminé")
        
    else:
        print("❌ Échec de connexion MQTT")
        return False
    
    return True

def send_test_commands():
    """Envoie des commandes de test"""
    print("🧪 Envoi de commandes de test...")
    
    mqtt_manager = MQTTManager()
    
    # Attendre la connexion
    timeout = 10
    start_time = time.time()
    while not mqtt_manager.is_connected() and (time.time() - start_time) < timeout:
        time.sleep(1)
    
    if mqtt_manager.is_connected():
        # Envoyer des commandes de test
        commands = [
            ("borne1/casier1", "1"),  # Ouvrir casier 1
            ("borne1/casier2", "1"),  # Ouvrir casier 2
            ("borne1/casier1", "0"),  # Fermer casier 1
            ("borne1/casier2", "0"),  # Fermer casier 2
        ]
        
        for topic, payload in commands:
            print(f"📤 Envoi: {topic} -> {payload}")
            mqtt_manager.client.publish(topic, payload, qos=1)
            time.sleep(2)
        
        mqtt_manager.disconnect()
        print("✅ Commandes envoyées")
    else:
        print("❌ Impossible de se connecter")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "send":
        send_test_commands()
    else:
        test_mqtt_connection()
