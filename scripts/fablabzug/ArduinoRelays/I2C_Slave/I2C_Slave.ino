#include <Wire.h>

// relay pins
int r1 = 4;
int r2 = 5;
int r3 = 6;
int r4 = 7;
int relays[] = { r1, r2, r3, r4 };

void setup()
{
  pinMode(r1, OUTPUT);
  pinMode(r2, OUTPUT);
  pinMode(r3, OUTPUT);
  pinMode(r4, OUTPUT);

  digitalWrite(r1, LOW);
  digitalWrite(r2, LOW);
  digitalWrite(r3, LOW);
  digitalWrite(r4, LOW);
  
  Wire.begin(4);                // join i2c bus with address #4
  Wire.onReceive(receiveEvent); // register event
  Serial.begin(9600);           // start serial for output

  // running relay checks
  digitalWrite(r1, HIGH);
  delay(500);
  digitalWrite(r2, HIGH);
  delay(500);
  digitalWrite(r3, HIGH);
  delay(500);
  digitalWrite(r4, HIGH);

  delay(2000);
  
  digitalWrite(r1, LOW);
  delay(500);
  digitalWrite(r2, LOW);
  delay(500);
  digitalWrite(r3, LOW);
  delay(500);
  digitalWrite(r4, LOW);
}

void loop()
{
  delay(100);
}

// function that executes whenever data is received from master
// this function is registered as an event, see setup()
void receiveEvent(int howMany)
{ 
  if(Wire.available())
  {
    int relayNr = Wire.read();
    int relayState = Wire.read();  
    
    Serial.print(relayNr);
    Serial.print(" : ");
    Serial.println(relayState);
    
    digitalWrite(relays[relayNr], relayState);
  }
}
