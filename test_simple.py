#!/usr/bin/env python3
"""
Script de test simple pour le système de casiers
"""

import time
from locker_manager import LockerManager
from mqtt_manager import MQTTManager

def test_system():
    """Test du système complet"""
    print("🧪 Test du système de casiers simplifié")
    
    # Initialiser les composants
    mqtt_manager = MQTTManager()
    locker_manager = LockerManager(mqtt_manager)
    
    # Attendre la connexion MQTT
    print("⏳ Attente connexion MQTT...")
    time.sleep(3)
    
    print(f"📡 MQTT connecté: {mqtt_manager.is_connected()}")
    
    # Test des codes
    print("\n🔑 Test des codes de déverrouillage:")
    
    # Test code correct casier 1
    print("Test casier 1 avec code 1234...")
    result = locker_manager.verify_code(0, "1234")
    print(f"Résultat: {'✅ Succès' if result else '❌ Échec'}")
    
    time.sleep(2)
    
    # Test code incorrect casier 1
    print("Test casier 1 avec code incorrect...")
    result = locker_manager.verify_code(0, "0000")
    print(f"Résultat: {'✅ Succès' if result else '❌ Échec (normal)'}")
    
    time.sleep(2)
    
    # Test code correct casier 2
    print("Test casier 2 avec code 5678...")
    result = locker_manager.verify_code(1, "5678")
    print(f"Résultat: {'✅ Succès' if result else '❌ Échec'}")
    
    print("\n⏱️ Attente 25 secondes pour voir l'auto-fermeture...")
    time.sleep(25)
    
    # Nettoyage
    locker_manager.cleanup()
    mqtt_manager.disconnect()
    
    print("✅ Test terminé")

if __name__ == "__main__":
    test_system()
