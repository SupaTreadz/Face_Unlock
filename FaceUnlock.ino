#include <FastLED.h>
#include <Servo.h>
#include <string.h>
//Connect USB port to Pi USB Port
//For serial debugging - connect to the RX1 and TX1 pins

#define NeopixelPin 6
#define NUM_LEDS 24
#define speakerPin 11
#define doorSensorPin 3
#define buttonPin 8
#define serialLED 12

CRGB leds[NUM_LEDS];
Servo lockServo;  // create servo object to control a servo
String test;

boolean doorLocked = false;
int buttonState = 0;
int buttonOld = 0;
boolean countdown = true;
unsigned long newTime = 0;
unsigned long UnlockTime = 0;
unsigned long oldtime;
int index = 0;
int oldindex = 0;
int pattern1 = 0;
boolean unlockindex = false;
volatile boolean interrupt = false;
char serIn;

void setup()
{
  pinMode(serialLED, OUTPUT);
  FastLED.addLeds<NEOPIXEL, NeopixelPin>(leds, NUM_LEDS);
  //Serial1.begin(9600);
  Serial.begin(9600);
  while (Serial.available()>0) serIn=Serial.read();
  Serial.setTimeout(50);
  digitalWrite(serialLED, HIGH);
  delay(1000);
  digitalWrite(serialLED, LOW);
  acceptTone();

  pinMode(doorSensorPin, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(doorSensorPin), doorOpen, RISING);
  
  pinMode(buttonPin, INPUT_PULLUP);
  buttonState = digitalRead(buttonPin);
  buttonOld = buttonState;

  lockServo.attach(9);
  lockServo.write(135);
  delay(500);
  doorLocked = true;
}

void loop()
{
  lockServo.detach();
  FastLED.show();

  if(millis() - oldtime > 100)
  {
    index = index + 1;
    if(unlockindex)
    {
      pattern1 = 3;
      unlockindex = false;
    }
    else
    {
      pattern1 = 0;
      unlockindex = true;
    }
    oldtime = millis();
  }
  
  if(doorLocked && index > NUM_LEDS-1)
  {
    index=0;
  }

  if(doorLocked)
  {
    if(index != oldindex)
    {
      leds[index] = CHSV(random8(),255,255);
      
      if(index==0)
      {
        leds[NUM_LEDS-1] = CRGB::Black;
        //leds[NUM_LEDS-1].fadeToBlackBy(90);
      }
      else
      {
        leds[index-1] = CRGB::Black;
        //leds[index-1].fadeToBlackBy(90);
      }
      oldindex = index;
    }
  }
  else
  {
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    leds[pattern1] = CRGB::Red;
    leds[pattern1+6] = CRGB::Red;
    leds[pattern1+12] = CRGB::Red;
    leds[pattern1+18] = CRGB::Red;
    
  }
  
  buttonState = digitalRead(buttonPin);

  if(buttonState != buttonOld)
  {
    if(!doorLocked)
    {
      fill_solid(leds, NUM_LEDS, CRGB::Purple);
      FastLED.show();
      lock();
      fill_solid(leds, NUM_LEDS, CRGB::Black);
      FastLED.show();
    }
    else
    {
      fill_solid(leds, NUM_LEDS, CRGB::Blue);
      FastLED.show();
      unlock();
      fill_solid(leds, NUM_LEDS, CRGB::Black);
      FastLED.show();
    }
    
    buttonOld = buttonState;
  }

  if(interrupt)
  {     
    while(digitalRead(doorSensorPin)==HIGH)
    {
      //fill_solid(leds, NUM_LEDS, CRGB::Yellow);
      flash(); 
      delay(500);
      //fill_solid(leds, NUM_LEDS, CRGB::Black);
    }
    
  }
  if (Serial.available()>0) 
  {
    serIn=Serial.read();
    if (serIn=='u') 
    { 
      acceptTone();
      if(doorLocked)
      {
        unlock();  
      }
    }
    else
    {
      rejectTone();
    }
    while (Serial.available()>0) serIn=Serial.read();
  } 
}
void acceptTone()
{
  fill_solid(leds, NUM_LEDS, CRGB::Green);
  FastLED.show();
  tone(speakerPin, 2610);
  delay(200);
  tone(speakerPin, 4150);
  delay(200);
  noTone(speakerPin);
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
}
void rejectTone()
{
  fill_solid(leds, NUM_LEDS, CRGB::Red);
  FastLED.show();
  tone(speakerPin, 1000);
  delay(200);
  tone(speakerPin, 370);
  delay(200);
  noTone(speakerPin);
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
}
void unlock()
{
  acceptTone();
  lockServo.attach(9);
  lockServo.write(30);
  //Serial.println("Locked");
  doorLocked = false;
  delay(500);
  lockServo.detach();
}
void lock()
{
  rejectTone();
  lockServo.attach(9);
  lockServo.write(135);
  //Serial.println("Locked");
  doorLocked = true;
  delay(500);
  lockServo.detach();
}
void doorOpen()
{
  interrupt = true;
}
void flash()
{
  tone(speakerPin, 300);
  fill_solid(leds, NUM_LEDS, CRGB::Yellow);
  FastLED.show();
  delay(50);
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  delay(50);
  noTone(speakerPin);
  fill_solid(leds, NUM_LEDS, CRGB::Yellow);
  FastLED.show();
  delay(50);
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  delay(50);
  fill_solid(leds, NUM_LEDS, CRGB::Yellow);
  FastLED.show();
  delay(50);
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  delay(50);
  
}
