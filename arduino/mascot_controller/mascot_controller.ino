#include <Servo.h>
#include <Adafruit_NeoPixel.h>

// ---------- Pins ----------
const int trigPin = 9;
const int echoPin = 10;
long duration;
float distance;

Servo myServo;

// ---------- LED STRIPS ----------
#define LED_PIN_1 6
#define LED_COUNT_1 15
Adafruit_NeoPixel strip1(LED_COUNT_1, LED_PIN_1, NEO_GRB + NEO_KHZ800);

#define LED_PIN_3 8
#define LED_COUNT_3 15
Adafruit_NeoPixel strip3(LED_COUNT_3, LED_PIN_3, NEO_GRB + NEO_KHZ800);

#define LED_PIN_2 7
#define LED_COUNT_2 10
Adafruit_NeoPixel strip2(LED_COUNT_2, LED_PIN_2, NEO_GRB + NEO_KHZ800);

// inner LEDs (pupil)
int innerLEDs[] = {4, 5, 8, 9};

bool isInner(int idx) {
  for (int i = 0; i < 4; i++)
    if (idx == innerLEDs[i])
      return true;
  return false;
}

// ----------------------------------------------------------
void setup() {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  Serial.begin(9600);
  Serial.setTimeout(10); 

  myServo.attach(11);
  myServo.write(30);
  delay(500);
  myServo.detach(); 

  strip1.begin(); strip1.show();
  strip2.begin(); strip2.show();
  strip3.begin(); strip3.show();
  
  Serial.println("Mascot Ready - Retro & Animated");
}

// ----------------------------------------------------------
long lastIdleTime = 0;
int idleState = 0; // 0=Normal, 1=Wink, 2=Happy/Blink

void loop() {
  // 1. Check for Serial Override
  if (Serial.available()) {
     String cmd = Serial.readStringUntil('\n');
     cmd.trim();
     
     if (cmd == "PHOTO") {
        photoFlash(); // Instant Flash
        return; 
     }
     else if (cmd == "LOVE") {
        emotionLove();
        lastIdleTime = millis(); // Reset idle timer
        return;
     }
     else if (cmd == "SUS") {
        emotionSus(); 
        lastIdleTime = millis();
        return;
     }
  }

  // 2. Ultrasonic Logic
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH, 30000); 

  if (duration == 0) distance = 999;
  else distance = (duration * 0.0343) / 2.0;

  if (distance > 0 && distance < 20) {
    emotionLove();
    lastIdleTime = millis();
    
    // Quick Servo Wave
    if(!myServo.attached()) myServo.attach(11);
    myServo.write(110); delay(100); myServo.write(30);
    delay(100);
    myServo.detach(); 
  }
  else if (distance >= 20 && distance < 60) {
    emotionSus();
    lastIdleTime = millis();
  }
  else {
    // IDLE MODE / NORMAL
    // Implement Random Idle Animations
    if (millis() - lastIdleTime > 6000) {
       // Every 6 seconds, pick a random animation
       int randAnim = random(0, 5); // 0-4
       if(randAnim == 1) emotionWink();
       else if(randAnim == 2) emotionHappyBlink();
       else emotionNormal();
       
       // Hold animation for a bit?
       if(randAnim != 0) { delay(1500); lastIdleTime = millis(); } 
       else { lastIdleTime = millis() - 3000; } // Shorter wait if we picked Normal
    } else {
       emotionNormal();
    }
  }
  
  delay(50); 
}

// =================== PHOTO FLASH (INSTANT) ===================
// =================== PHOTO FLASH (Key Change: SLOW LOVE BLINK) ===================
void photoFlash() {
  // User requested "blink the love imojie... little bit slow"
  if(!myServo.attached()) myServo.attach(11);
  myServo.write(110); // Wave
  
  for(int k=0; k<2; k++){
      emotionLove(); // Show Love Pulse
      delay(600);    // Slow hold (0.6s)
      
      strip1.clear(); strip3.clear();
      strip1.show(); strip3.show();
      delay(300);    // Off interval
  }
  
  myServo.write(30);
  delay(200);
  myServo.detach();
}

// =================== LOVE MODE ===================
void emotionLove() {
  int loveIdx[] = {0, 2, 3, 4, 5, 6, 7, 10, 11, 13, 14};
  uint32_t pink = strip1.Color(255, 20, 147);
  uint32_t white = strip1.Color(255, 255, 255);

  strip1.clear(); strip3.clear(); 

  for (int i = 0; i < sizeof(loveIdx)/sizeof(loveIdx[0]); i++) {
    int idx = loveIdx[i];
    bool pupil = (idx == 4 || idx == 5);
    strip1.setPixelColor(idx, pupil ? white : pink);
    strip3.setPixelColor(idx, pupil ? white : pink);
  }
  strip1.show(); strip3.show();
}

// =================== SUS MODE (SMOOTHER) ===================
void emotionSus() {
  int susLeds[] = {3,4,5,6,7,8,9,10};
  
  // SLOWER BREATHING
  // millis()/600.0 makes the wave 3x wider/slower than 200.0
  float val = (exp(sin(millis()/600.0*PI)) - 0.36787944)*108.0; 
  int brightness = (int)val;
  if(brightness > 255) brightness = 255;
  if(brightness < 10) brightness = 10; // Min brightness
  
  uint32_t color = strip1.Color(brightness, (brightness*200)/255, 0);

  strip1.clear(); strip3.clear();
  for (int i = 0; i < 8; i++) {
     strip1.setPixelColor(susLeds[i], color);
     strip3.setPixelColor(susLeds[i], color);
  }
  strip1.show(); strip3.show(); // Removed delay(20) to avoid blocking main loop too much if called often
}
void emotionNormal() {
  strip1.clear(); strip3.clear();
  uint32_t redDim = strip1.Color(120, 0, 0);
  
  // Calculate Slow Blink/Breathing for Inner LEDs
  // sin wave based on time (approx 2s period)
  float breath = (exp(sin(millis()/800.0*PI)) - 0.36787944)*108.0;
  int bVal = (int)breath;
  if(bVal > 255) bVal = 255; 
  if(bVal < 10) bVal = 10;
  
  uint32_t yellowBlink = strip1.Color(bVal, (bVal*200)/255, 0); // Preserve Yellow Ratio

  // Outer LEDs Static Red
  for (int i = 0; i < 15; i++) {
    if (i == 14) continue; 
    if (!isInner(i)) {
      strip1.setPixelColor(i, redDim);
      strip3.setPixelColor(i, redDim);
    }
  }
  // Inner LEDs Blinking Yellow
  for (int i = 0; i < 4; i++) {
    strip1.setPixelColor(innerLEDs[i], yellowBlink);
    strip3.setPixelColor(innerLEDs[i], yellowBlink);
  }
  strip1.show(); strip3.show();
}

// =================== WINK ANIMATION ===================
void emotionWink() {
  // Left eye (Strip 1) Closes (turns off or line)
  // Right eye (Strip 3) stays Normal
  strip1.clear(); // Close Left Eye
  
  // Draw Line on Left Eye (Eyelid closed)
  // 6, 7, 8, 9 are bottom? 
  strip1.setPixelColor(7, strip1.Color(100,0,0)); 
  strip1.setPixelColor(8, strip1.Color(100,0,0));

  // Right Eye Normal
  uint32_t redDim = strip3.Color(120, 0, 0);
  uint32_t yellow = strip3.Color(255, 200, 0);
  
  strip3.clear();
  for (int i = 0; i < 15; i++) {
    if (i == 14) continue; 
    if (!isInner(i)) strip3.setPixelColor(i, redDim);
  }
  for (int i = 0; i < 4; i++) strip3.setPixelColor(innerLEDs[i], yellow);

  strip1.show(); strip3.show();
}

// =================== HAPPY BLINK ===================
void emotionHappyBlink() {
  // Both eyes blink rapidly twice
  for(int j=0; j<2; j++) {
     strip1.clear(); strip3.clear();
     strip1.show(); strip3.show();
     delay(150);
     emotionNormal();
     delay(150);
  }
}
