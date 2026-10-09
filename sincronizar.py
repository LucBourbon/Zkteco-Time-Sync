import win32com.client
import datetime
import logging
import os
import json

# --- Configuración del Logging ---
log_file_path = "sincronizador_log.txt" # El log se creará en la misma carpeta del ejecutable
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO, # Puedes cambiar a logging.DEBUG para más detalle
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Configuración de tus Dispositivos ZKTeco ---
with open("dispositivos.json", "r", encoding="utf-8") as f:
    dispositivos = json.load(f)

def sincronizar_hora_dispositivo(ip, puerto, numero_maquina):
    """
    Función para conectar, sincronizar la hora y desconectar de un dispositivo ZKTeco.
    """
    logging.info(f"\nIntentando conectar con el dispositivo {ip}:{puerto} (Máquina #{numero_maquina})...")

    try:
        zk = win32com.client.Dispatch("ZKEMKeeper.ZKEM.1")
    except Exception as e:
        logging.error(f"Error al crear el objeto ZKEMKeeper: {e}")
        logging.error("Asegúrate de que zkemkeeper.dll esté correctamente registrada (ejecutar registrar_sdk.bat como administrador) y que la arquitectura de Python sea 32-bit.")
        return False

    if zk.Connect_Net(ip, puerto):
        logging.info(f"Conexión exitosa con {ip}.")

        if zk.SetDeviceTime(numero_maquina):
            logging.info(f"Hora del dispositivo {ip} sincronizada con éxito a la hora del servidor.")
        else:
            error_code = zk.GetLastError()
            logging.error(f"Error: No se pudo sincronizar la hora del dispositivo {ip}. Código de error: {error_code}")

        zk.Disconnect()
        logging.info(f"Desconectado de {ip}.")
        return True
    else:
        error_code = zk.GetLastError()
        logging.error(f"Error al conectar con {ip}. Código de error: {error_code}")
        logging.error("Posibles causas: IP incorrecta, dispositivo apagado, puerto bloqueado (firewall), problema de red.")
        return False

# --- Lógica principal del Script ---
if __name__ == "__main__":
    logging.info(f"Script de sincronización de hora ZKTeco iniciado - {datetime.datetime.now()}")

    for disp in dispositivos:
        sincronizar_hora_dispositivo(disp["ip"], disp["puerto"], disp["numero_maquina"])

    logging.info("Proceso de sincronización de hora ZKTeco finalizado.")