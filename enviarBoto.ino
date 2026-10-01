#include <SPI.h>
#include <LoRa.h>
#include <MKRWAN.h>

LoRaModem modem;
String appEui = "0000000000000000"; 
String appKey = "TU_APP_KEY"; 
String devEui = "A8610A33391B8511";

int counter = 0;
int data = 0; 

void setup() {
  Serial1.begin(9600); 
  while (!Serial);
  if (!modem.begin(EU868)) {
    while(1);
  }
  int connected = modem.joinOTAA(appEui, appKey, devEui);
    if (!connected) {
      while (!modem.joinOTAA(appEui, appKey, devEui)) {
        delay(10000);
      }
    }
modem.minPollInterval(60);
}
void loop() {
  if (Serial.available() > 0) {
    char datoRecibido = Serial.read();
    String jsonData = "{\"temp\":25,\"hum\":60}";
    modem.beginPacket();
    modem.write((uint8_t*)jsonData.c_str(), jsonData.length());
    int err = modem.endPacket(true); // true = envío confirmado (ACK)
    if (err > 0) {
      Serial.println("Message sent!");
    } 
    else {
      Serial.print("Error while sending. Code: ");
      Serial.println(err);  
    }
    // Esperar posible downlink
    delay(1000);
    char rcv[64];
    int i = 0;
    while (modem.available()) {
      rcv[i++] = (char)modem.read();
    }
    Serial.print("Received: ");
    for (unsigned int j = 0; j < i; j++) {
      Serial.print(rcv[j] >> 4, HEX);
      Serial.print(rcv[j] & 0xF, HEX);
      Serial.print(" ");
    }
    Serial.println();
    }
  }
