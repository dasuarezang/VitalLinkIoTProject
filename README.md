# VitalLink IoT

Sistema IoT de monitorización de frecuencia cardíaca de extremo a extremo: un sensor **BITalino** capta la señal ECG, una **Raspberry Pi** calcula los BPM, un **Arduino MKR WAN** los envía por **LoRaWAN** a **The Things Network**, **Node-RED** los guarda en **Supabase (PostgreSQL)** y un dashboard en **Next.js** los muestra en tiempo real.

## Arquitectura

```
┌──────────┐ Bluetooth ┌──────────────┐  UART   ┌──────────────┐ LoRaWAN ┌─────────┐  MQTT  ┌──────────┐  SQL  ┌──────────┐       ┌───────────┐
│ BITalino │ ────────► │ Raspberry Pi │ ──────► │ Arduino MKR  │ ──────► │   TTN   │ ─────► │ Node-RED │ ────► │ Supabase │ ────► │ Dashboard │
│  (ECG)   │           │  (Python)    │ ◄────── │  WAN (EU868) │ ◄────── │ (v3)    │ ◄───── │          │       │ Postgres │       │  Next.js  │
└──────────┘           └──────────────┘         └──────────────┘         └─────────┘        └──────────┘       └──────────┘       └───────────┘
                         BPM → JSON               uplink / downlink        decoder JS         INSERT + downlink                      Recharts
```

### Flujo de datos

1. **Adquisición:** la Raspberry Pi se conecta al BITalino por Bluetooth (`/dev/rfcomm0`) y lee el canal analógico A1 (ECG) a 100 Hz.
2. **Procesado:** cada ventana de 10 s se procesa con `biosppy` (filtro paso banda, detección de picos R con Hamilton y cálculo del intervalo RR) para obtener los BPM.
3. **Agregación:** los BPM se acumulan durante 10 minutos y se envía la media como JSON:
   ```json
   { "timestamp": 1762943705.4, "sensor": "ECG", "bpm": 72 }
   ```
4. **Uplink:** el JSON llega por UART (`/dev/ttyS0`, 9600 baudios) al Arduino MKR WAN, que lo transmite como mensaje LoRaWAN confirmado (OTAA, banda EU868).
5. **Decodificación:** el *payload formatter* de TTN convierte los bytes a texto y lo parsea como JSON.
6. **Persistencia:** Node-RED se suscribe al MQTT de TTN y guarda cada medida en la tabla `sensor_data` de Supabase.
7. **Visualización:** el dashboard consulta `sensor_data` cada segundo y dibuja la frecuencia cardíaca con Recharts.
8. **Downlink:** Node-RED puede enviar un comando (`0x01`) al dispositivo, que el Arduino reenvía por UART a la Raspberry Pi.

## Estructura del repositorio

| Archivo / carpeta | Descripción |
|---|---|
| `bitalino_final.py` | Script principal de la Raspberry Pi: lectura ECG, cálculo de BPM, envío por UART y lectura del downlink |
| `bitalinov.py`, `bitalinov1.py`, `bitalinovprueba` | Versiones anteriores y pruebas del script de adquisición |
| `ArduinoFinal.ino` | Firmware final del MKR WAN: recibe JSON por UART, envía uplink y devuelve el downlink en hexadecimal por UART |
| `CodiArduino.ino` | Versión solo uplink (UART → LoRaWAN) |
| `codiArduinoDownlinkUART.ino` | Versión intermedia con recepción de downlink |
| `enviarBoto.ino` | Prueba inicial: envía un JSON fijo al recibir un carácter por el puerto serie |
| `UPLINK_PAYLOAD_FORMATER` | Decoder JavaScript para TTN (`decodeUplink`) |
| `NODE_RED_FUNCION_CODE` | Nodo *function* de Node-RED que crea el `INSERT` para PostgreSQL |
| `DOWNLINK_NODE_RED` | Nodo *function* de Node-RED que publica un downlink en TTN |
| `app/`, `components/` | Dashboard web (Next.js App Router + Supabase Auth + Recharts) |
| `datos-vitalino_live_data_*.json` | Captura de datos reales de TTN (eventos `as.up.data.forward`) |

## Hardware

- BITalino (r)evolution con sensor ECG
- Raspberry Pi (Bluetooth + UART)
- Arduino MKR WAN 1300/1310 con antena LoRa
- Gateway LoRaWAN conectado a The Things Network

## Puesta en marcha

### 1. Raspberry Pi

```bash
pip install bitalino biosppy numpy pyserial
# Emparejar el BITalino y crear el puerto /dev/rfcomm0
python3 bitalino_final.py
```

### 2. Arduino MKR WAN

1. Instala la librería **MKRWAN** desde el gestor de librerías del IDE de Arduino.
2. Registra el dispositivo en TTN (OTAA) y pon tus `appEui`, `appKey` y `devEui` en `ArduinoFinal.ino`.
3. Conecta el UART del Arduino (`Serial1`, pines 13/14) al de la Raspberry Pi con masa común y carga el sketch.

### 3. The Things Network

En la aplicación de TTN, en *Payload formatters → Uplink → Custom JavaScript*, pega el contenido de `UPLINK_PAYLOAD_FORMATER`.

### 4. Supabase

```sql
create table sensor_data (
  id            bigint generated always as identity primary key,
  payload       jsonb,
  created_at    timestamp,
  frec_cardiaca integer
);
```

### 5. Node-RED

- **Uplink:** `mqtt in` (broker de TTN, topic `v3/<app-id>@<tenant>/devices/+/up`) → `json` → *function* con `NODE_RED_FUNCION_CODE` → nodo PostgreSQL apuntando a Supabase.
- **Downlink:** `inject` → *function* con `DOWNLINK_NODE_RED` → `mqtt out` al broker de TTN.

### 6. Dashboard

El código web parte de la plantilla oficial de Next.js con Supabase. Para ejecutarlo:

```bash
npx create-next-app -e with-supabase vitallink-dashboard
# Copia app/ y components/ de este repositorio dentro del proyecto
npm install recharts
```

Rellena `.env.local` con la URL y la clave pública de tu proyecto de Supabase (las variables que indica la plantilla) y arranca con `npm run dev`.

## Tecnologías

**Hardware:** BITalino · Raspberry Pi · Arduino MKR WAN
**Comunicaciones:** Bluetooth · UART · LoRaWAN · MQTT
**Backend:** The Things Network v3 · Node-RED · Supabase (PostgreSQL)
**Software:** Python (biosppy, NumPy, pySerial) · C++/Arduino · JavaScript · TypeScript · Next.js · React · Tailwind CSS · Recharts
