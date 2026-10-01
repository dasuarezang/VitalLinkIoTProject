import json
import serial
import time
import numpy as np
from bitalino import BITalino
from biosppy.signals import ecg
import sys

# --- Configuración ---
mac_address = "/dev/rfcomm0"
device = None
arduino = None

# IMPORTANTE: Samplerate subido a 100 para que funcione biosppy
samplerate = 100 
WINDOW_SIZE_SECONDS = 30
BUFFER_SIZE = samplerate * WINDOW_SIZE_SECONDS 

# Inicializamos variable bpm para evitar error de referencia
bpm = 0

try:
    print(f"Conectando a BITalino en {mac_address}...")
    device = BITalino(mac_address)
    device.start(samplerate, [1]) 
    print("BITalino iniciado.")
    
    print("Conectando a Arduino...")
    arduino = serial.Serial("/dev/ttyS0", 9600, timeout=1)
    time.sleep(2)

    ecg_buffer = []
    lecturas_tomadas = 0 

    print(f"Llenando buffer inicial de {WINDOW_SIZE_SECONDS} segundos...")

    while True:
        # 1. LEER DATOS
        nummuestras = samplerate
        data = device.read(nummuestras)
        lecturas_tomadas += 1
        
        # 2. EXTRAER Y ACUMULAR
        new_samples = [row[5] for row in data]
        ecg_buffer.extend(new_samples)
        
        # 3. MANTENER EL TAMAÑO DEL BUFFER
        if len(ecg_buffer) > BUFFER_SIZE:
            ecg_buffer = ecg_buffer[-BUFFER_SIZE:]
            
        # 4. PROCESAR
        # Esperamos a tener al menos 5 segundos de datos reales (500 muestras a 100Hz)
        min_samples = 5 * samplerate
        
        if len(ecg_buffer) >= min_samples:
            try:
                signal_to_process = np.array(ecg_buffer)
                
                # Procesamos con biosppy
                out = ecg.ecg(signal=signal_to_process, sampling_rate=samplerate, show=False)
                
                if len(out['heart_rate']) > 0:
                    bpm = int(np.mean(out['heart_rate']))
                    sys.stdout.write(f"\rBuffer: {len(ecg_buffer)} | BPM: {bpm}   ")
                    sys.stdout.flush()
                else:
                    sys.stdout.write(f"\rBuffer: {len(ecg_buffer)} | BPM: Calculando... ")
                    sys.stdout.flush()
                    
            except Exception as e:
                # Importante imprimir el error para depurar
                # print(f"Error biosppy: {e}") 
                pass
        else:
             sys.stdout.write(f"\rCargando buffer: {len(ecg_buffer)}/{BUFFER_SIZE}...")
             sys.stdout.flush()

        # 5. ENVIAR A ARDUINO
        # Enviamos cada vez que se llene un bloque del tamaño del buffer (o ajústalo a lo que necesites)
        # Nota: Enviar cada 1500 lecturas es muy lento. Quizás prefieras enviar cada 100 (1 seg).
        if len(ecg_buffer) >= BUFFER_SIZE: 
            sample = {
                "timestamp": time.time(),
                "sensor": "ECG",
                "bpm": bpm
                #"raw": int(new_samples[-1]) 
            }
            ecg_buffer = []
            json_data = json.dumps(sample)
            print("\n\nSending: " + str(json_data)+"\n\n") 
            
            if arduino:
                arduino.write((json_data + '\n').encode("utf-8"))
                
                # 2. RECIBIR RESPUESTA (DOWNLINK)
                # Damos un pequeñísimo margen para que Arduino procese (opcional)
                time.sleep(0.5) 
                # Comprobamos si hay datos esperando en el puerto serie
                if arduino.in_waiting > 0:
                    try:
                        # Leemos la línea que envía el Arduino
                        respuesta_raw = arduino.readline()
                        respuesta = respuesta_raw.decode('utf-8', errors='ignore').strip()
                        print(f"--> RECIBIDO DEL ARDUINO: {respuesta}")
                        
                        # Aquí puedes procesar la respuesta (ej: cambiar configuración)
                        if "ALERTA" in respuesta:
                            print("!!! El Arduino ha enviado una alerta !!!")
                            
                    except Exception as e_serial:
                        print(f"Error leyendo respuesta: {e_serial}")

except KeyboardInterrupt:
    print("\nDeteniendo...")
except Exception as e:
    print(f"\nERROR GENERAL: {e}")
finally:
    if device:
        device.stop()
        device.close()
    if arduino:
        arduino.close()
