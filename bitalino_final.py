import json
import serial
import time
import numpy as np
from bitalino import BITalino
from biosppy.signals import ecg
import sys


###BLOQUE DECLARACIONES
#Configuracion y declaración de variables
mac_address = "/dev/rfcomm0"
device = None
arduino = None

#Definicion de tasa de muestro y tiempos
samplerate = 100 
WINDOW_SIZE_SECONDS = 10 
WINDOW_BPM_SIZE_MINUTES = 10

BUFFER_SIZE = samplerate * WINDOW_SIZE_SECONDS 
BUFFER_SIZE_BPM = int((60 / WINDOW_SIZE_SECONDS) * WINDOW_BPM_SIZE_MINUTES)

bpm = 0
    

try:
    ###BLOQUE CONEXIONES
    print(f"Conectando a BITalino en {mac_address}...")
    device = BITalino(mac_address)
    #Inciamos la conexion con el Bitalino
    device.start(samplerate, [1]) 
    print("BITalino iniciado.")
    
    print("Conectando a Arduino...")
    #Inciamos la conexion con el Arduino
    arduino = serial.Serial("/dev/ttyS0", 9600, timeout=1)
    #Tiempo de seguridad para la conexion
    time.sleep(2)
    
    
    ###BLOQUE MEDIDAS Y BUFFER
    ecg_buffer = []
    bpm_buffer = []

    print(f"Llenando buffer inicial de {WINDOW_SIZE_SECONDS} segundos...")

    while True:
        #Leemos datos
        data = device.read(samplerate)
        
        #Añadimos al buffer 
        #Leemos la columna 5 del Bitalino que es el canal analogico 1, que es la del ECG
        new_samples = [row[5] for row in data] 
        ecg_buffer.extend(new_samples)
        
        #Comprobamos que buffer no sobrepasa capacidad y si no eliminamos muestras antiguas
        if len(ecg_buffer) > BUFFER_SIZE:
            ecg_buffer = ecg_buffer[-BUFFER_SIZE:]
            
        #Procesamos datos
        #Muestras necesarias para calcular ecg
        min_samples = WINDOW_SIZE_SECONDS * samplerate
        
        if len(ecg_buffer) >= min_samples:
            try:
                #Convertimos a array numpy para biosppy (necesario para que biosppy pueda trabajar)
                signal_to_process = np.array(ecg_buffer) 
                
                #Procesamos con biosppy para obtener BPM
                out = ecg.ecg(signal=signal_to_process, sampling_rate=samplerate, show=False) 

                #Que hace la libreria BIOSSPY para calcular los BPM's?
                #1: Filtro paso banda: Eliminamos freciencias bajas y altas que no pertenecen a los bpms
                #2: Encuentra los picos: Aplica algoritmo de Hamilton/Christov para buscar picos los cuales su forma coincida con un latido
                #3: Calculo de intervalo: Calcula las muestras entre pico y pico, las pasa a tiempo
                #4: Calculo de la frecuencia (BPM's): 60s/minuto / T = BPMS

                #Si detectamos ritmo cardiaco lo calculamos
                #'heart_rate' es un indice que usamos para obtener el dato que nos interesa de out (out contiene: señal filtrada, picos cardiacos y el propio ritmo cardiaco)
                if len(out['heart_rate']) > 0:  
                    bpm = int(np.mean(out['heart_rate']))
                    
                    #Usamos append para guardar el dato en el vector
                    bpm_buffer.append(bpm)

                    #Vaciamos buffer para proximas iteraciones
                    ecg_buffer = [] 
                    
                    #Mostramos progreso de llenado del tiempo total
                    sys.stdout.write(f"\rMuestras guardadas: {len(bpm_buffer)}/{BUFFER_SIZE_BPM} | BPM Actual: {bpm}    ")
                    sys.stdout.flush()
                else:
                    sys.stdout.write(f"\rBuffer: {len(ecg_buffer)} | BPM: Calculando... ")
                    sys.stdout.flush()
                    
            except Exception as e:
                #Vemos el error si ocurre
                print(f"Error calculando BPM: {e}")
                pass
        else:
             sys.stdout.write(f"\rCargando buffer de 10s: {len(ecg_buffer)}/{BUFFER_SIZE}...")
             sys.stdout.flush()
            
        #Enviamos al arduino solo cuando tengamos las muestras del tiempo deseado completas
        if len(bpm_buffer) >= BUFFER_SIZE_BPM:    
            sample = {
                "timestamp": time.time(),
                "sensor": "ECG",
                "bpm": int(np.mean(bpm_buffer))
            }
            
            #Vaciamos buffer para el siguiente margen de tiempo
            bpm_buffer = [] 
    
            
            ###BLOQUE UPLINK (ENVIO JSON)
            json_data = json.dumps(sample) #creamos el JSON
            print("\n\n--- MINUTO COMPLETADO. ENVIANDO ---")
            print("Sending: " + str(json_data)+"\n") 
            
            if arduino:
                arduino.write((json_data + '\n').encode("utf-8"))
                
                # RECIBIR RESPUESTA (DOWNLINK)
                #Damos un pequeño margen para que Arduino procese 
                time.sleep(0.5) 
                #Comprobamos si hay datos esperando en el puerto serie
                if arduino.in_waiting > 0:
                    try:
                        # Leemos la línea que envía el Arduino
                        respuesta_raw = arduino.readline()
                        respuesta = respuesta_raw.decode('utf-8', errors='ignore').strip()
                        print(f"--> RECIBIDO DEL ARDUINO: {respuesta}")
                        
                        if "ALERTA" in respuesta:
                            print("!El Arduino ha enviado una alerta!")
                            
                    except Exception as e_serial:
                        print(f"Error leyendo respuesta: {e_serial}")

###BLOQUE EXCEPCIONES GENERALES        
except KeyboardInterrupt:
    #Para parar el código con CTRL+C
    print("\nDeteniendo...")
except Exception as e:
    print(f"\nERROR GENERAL: {e}")
finally:
    #Cerramos Bitalino y Arduino si estan abiertos
    if device: 
        device.stop()
        device.close()
    if arduino:
        arduino.close()
