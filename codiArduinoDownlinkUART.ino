#include <SPI.h>
#include <LoRa.h>
#include <MKRWAN.h>

LoRaModem modem;
String appEui = "0000000000000000"; 
String appKey = "TU_APP_KEY"; 
String devEui = "A8610A33391B8511";

int counter = 0;
int data = 0; 
char rcv[128];
int len = 0;

void setup() {
  Serial1.begin(9600); //UART
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
  len = 0; 
    // Esperar a recibir un JSON terminado en '\n'
    if (Serial1.available()) {
      //Lee hasta \n 
      len = Serial1.readBytesUntil('\n', rcv, sizeof(rcv) - 1);
      //Elimina posible \r final si existe
      if (len > 0 && rcv[len - 1] == '\r') {
        len--;
      }
      rcv[len] = '\0';  //Forzamos que acabe \0

      if(len > 1){
        modem.beginPacket();
        modem.print(rcv);
        int err = modem.endPacket(true); //true = envío confirmado (ACK)
        if (err > 0) {
          Serial1.println("Message sent!");
        } else {
        Serial1.print("Error while sending. Code: ");
        Serial1.println(err);  
        }
    }
    delay(1000);
    //Esta parte es una adaptación del ejemplo LoRaSendAndReceive
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

