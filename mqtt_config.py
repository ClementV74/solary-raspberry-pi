"""
Configuration MQTT centralisée
"""

# Configuration HiveMQ Cloud
MQTT_CONFIG = {
    "server": "713ba7b64fc64ce1b65c6a52ccda09dd.s1.eu.hivemq.cloud",
    "port": 8883,
    "username": "solary",
    "password": "Reseal0-Smokeless9-Peso5-Graceless4-Trustable0",
    "use_tls": True,
    "client_id": "solary_borne1",
    "keepalive": 60,
    "qos": 1
}

# Topics MQTT
MQTT_TOPICS = {
    "base": "borne1",
    "casier1": "borne1/casier1",
    "casier2": "borne1/casier2", 
    "status": "borne1/status",
    "casiers_status": "borne1/casiers/status"
}

# Commandes MQTT
MQTT_COMMANDS = {
    "OPEN": 1,
    "CLOSE": 0
}

# Actions
MQTT_ACTIONS = {
    "UNLOCK": "unlock",
    "LOCK": "lock", 
    "RESERVE": "reserve",
    "TEST": "test"
}

# Statuts
MQTT_STATUS = {
    "ONLINE": "online",
    "OFFLINE": "offline",
    "MAINTENANCE": "maintenance",
    "AVAILABLE": "available",
    "OCCUPIED": "occupied"
}
