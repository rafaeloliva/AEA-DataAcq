/*
  Modbus RTU Server LED

  This sketch creates a Modbus RTU Server with a simulated coil.
  The value of the simulated coil is set on the LED

  Circuit:
   - MKR board
   - MKR 485 shield
     - ISO GND connected to GND of the Modbus RTU server
     - Y connected to A/Y of the Modbus RTU client
     - Z connected to B/Z of the Modbus RTU client
     - Jumper positions
       - FULL set to OFF
       - Z \/\/ Y set to OFF

  created 16 July 2018
  by Sandeep Mistry
  //Changed to 19200 RO 21-3-21
  //Changed to Fixed values 25.3.21 - Funciona ok
  Version b - 29.07.2021 R.Oliva - added ESP32/DHT access from
  MIOT DAppIoT program: 
  D:\FromBigi5\MIoT2020\Materias\DApp3\TPFinalDAPP3\para_repo\VSC_ESP32+DHT\src\esp32_dht11a.cpp
  Version c -To work on Arduino Mega / PIO +29A412 Project 5.8.21
*/

#include <ArduinoRS485.h> // ArduinoModbus depends on the ArduinoRS485 library
#include <ArduinoModbus.h>
#include "DHT.h"

// Digital pin connected to the DHT sensor
// Use same as Patricio's diagram - was 4
#define DHTPIN 2

// Led builtin
// #define LED_BUILTIN 2 (ESP32)

// Uncomment whatever DHT sensor type you're using
//#define DHTTYPE DHT11   // DHT 11
#define DHTTYPE DHT22     // DHT 22  (AM2302), AM2321 2.10.20
//#define DHTTYPE DHT21   // DHT 21 (AM2301)   

#define OK_STATUS 1

// Initialize DHT sensor
DHT dht(DHTPIN, DHTTYPE);

// Variables to hold sensor readings
float temp;
float hum;

// Timing Added from ESP32 version - changed to 2 s
unsigned long previousMillis = 0;   // Stores last time temperature was published
const long interval = 2000;         // Interval 2sec at which to publish sensor readings


const int ledPin = LED_BUILTIN;
const int numHoldingRegisters = 3;
int regVal[3];  // Arrays are 0 - indexed
int coilValue = 1;

void setup() {
  Serial.begin(19200);
  dht.begin();

  Serial.println("Modbus RTU Server LED + HoldingRegs");
  regVal[0]=1234;
  regVal[1]=4567;
  regVal[2]=25;

  // (A0) Inicializacion común

  delay(2000);
// start the Modbus RTU server, with (slave) id 1
 if (!ModbusRTUServer.begin(1, 19200)) {
    Serial.println("Failed to start Modbus RTU Server!");
    while (1);
 }

  // configure the LED
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  // configure a single coil at address 0x00
  // ModbusRTUServer.configureCoils(0x00, 1);
  // configure holding registers at address 0x00
  ModbusRTUServer.configureHoldingRegisters(0x00, numHoldingRegisters);

  
}

void loop() {
  
  // (A1) Replace with new readings from DHT22
  // Arrange timing first:
  unsigned long currentMillis = millis();
  // Every X number of seconds (interval = 2 seconds) 
  // it Reads DHT and updates table values
  if (currentMillis - previousMillis >= interval) {
    // Save the last time a new reading was published
    previousMillis = currentMillis;
    // New DHT sensor readings
    hum = dht.readHumidity();
    // Read temperature as Celsius (the default)
    temp = dht.readTemperature();

    // Check if any reads failed 
	// Signal values to alarm
    if (isnan(temp) || isnan(hum)) {
      // Serial.println(F("Failed to read from DHT sensor!"));
        regVal[0]=4444;
        regVal[1]=5555;
        regVal[2]=66;   
    }
  }  // End Timing if..
  // poll for Modbus RTU requests
  
  ModbusRTUServer.poll();

  // (A2) Aquí se actualizan los valores de 
  regVal[0]=(int)(10.0*temp); // Temperatura_Inver;
  regVal[1]=(int)(10.0*hum); // Humedad_Inver;
  regVal[2]= OK_STATUS;    // no further changes..
  if (coilValue) {
    // coil value set, turn LED on
    digitalWrite(ledPin, HIGH);
    coilValue=0;
  } else {
    // coil value clear, turn LED off
    digitalWrite(ledPin, LOW);
    coilValue=1;
  }

 // map the holding register values to the input register values
 // map the holding register values to the input register values
  for (int i = 0; i < numHoldingRegisters; i++) {
    //long Value  = i+ModbusRTUServer.holdingRegisterRead(i);

    //ModbusRTUServer.inputRegisterWrite(i, holdingRegisterValue);
    ModbusRTUServer.holdingRegisterWrite(i, regVal[i]);
  }
  // read the current value of the coil
  // int coilValue = ModbusRTUServer.coilRead(0x00);
  
  // delay(500);
  // v_v 5.8.21 - move LED toggle to if(millis) condition
//  if (coilValue) {
//    // coil value set, turn LED on
//    digitalWrite(ledPin, HIGH);
//    coilValue=0;
//  } else {
//    // coil value clear, turn LED off
//    digitalWrite(ledPin, LOW);
//    coilValue=1;
//  }
  // delay(200); - eliminate delay 5.8.21 vc
}
