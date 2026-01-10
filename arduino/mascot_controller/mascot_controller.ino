#include <Adafruit_NeoPixel.h>

// ---------- Ultrasonic Sensor Pins ----------
const int trigPin = 9;
const int echoPin = 10;
long duration;
float distance;
float lastValidDistance = 999;  // Store last valid reading for smoothing
int invalidReadingCount = 0;    // Count consecutive invalid readings
const int MAX_INVALID_READINGS = 5; // How many 999s before switching to idle

// ---------- LED STRIPS (2 EYES ONLY) ----------
// LEFT EYE - Pin 7
#define LED_PIN_LEFT 7
#define LED_COUNT_LEFT 15
Adafruit_NeoPixel leftEye(LED_COUNT_LEFT, LED_PIN_LEFT, NEO_GRB + NEO_KHZ800);

// RIGHT EYE - Pin 8
#define LED_PIN_RIGHT 8
#define LED_COUNT_RIGHT 15
Adafruit_NeoPixel rightEye(LED_COUNT_RIGHT, LED_PIN_RIGHT, NEO_GRB + NEO_KHZ800);

// Inner LEDs (pupil) - center of the eye
int innerLEDs[] = {4, 5, 8, 9};

bool isInner(int idx) {
  for (int i = 0; i < 4; i++)
    if (idx == innerLEDs[i])
      return true;
  return false;
}

// ----------------------------------------------------------
// STEPPER MOTOR (NEMA 17 + TB6600) - For waving hand
// ----------------------------------------------------------
#define STEP_PIN 2
#define DIR_PIN 3
#define ENA_PIN 4

// Stepper Configuration - SLOW bye-bye wave (~80% movement)
const int stepsPerWave = 80;    // ~80% movement (was 60)
const int stepDelay = 4500;     // Slow speed

void waveStepper() {
  // Enable the driver
  digitalWrite(ENA_PIN, LOW);

  // 2 waves for bye-bye gesture
  for(int k = 0; k < 2; k++) {
    // Clockwise - slow wave
    digitalWrite(DIR_PIN, HIGH);
    for(int x = 0; x < stepsPerWave; x++) {
      digitalWrite(STEP_PIN, HIGH);
      delayMicroseconds(stepDelay);
      digitalWrite(STEP_PIN, LOW);
      delayMicroseconds(stepDelay);
    }
    
    delay(300); // Pause at end

    // Counter-Clockwise - slow wave back
    digitalWrite(DIR_PIN, LOW);
    for(int x = 0; x < stepsPerWave; x++) {
      digitalWrite(STEP_PIN, HIGH);
      delayMicroseconds(stepDelay);
      digitalWrite(STEP_PIN, LOW);
      delayMicroseconds(stepDelay);
    }
    delay(300);
  }

  // Disable to save power
  digitalWrite(ENA_PIN, HIGH);
}

// ----------------------------------------------------------
void setup() {
  // Ultrasonic pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  // Stepper pins
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ENA_PIN, OUTPUT);
  digitalWrite(ENA_PIN, HIGH); // Start Disabled
  
  Serial.begin(9600);
  Serial.setTimeout(10); 

  // Initialize both eye strips
  leftEye.begin();
  leftEye.setBrightness(255);
  leftEye.show();
  
  rightEye.begin();
  rightEye.setBrightness(255);
  rightEye.show();
  
  // Test both eyes on startup
  testEyes();
  
  Serial.println("Mascot Ready - Stepper Only (No Servo)");
  Serial.println("Pins: Left Eye=7, Right Eye=8, Stepper=2,3,4, Ultrasonic=9,10");
}

// Test function to verify both eyes work
void testEyes() {
  Serial.println("Testing LEFT eye (Pin 7)...");
  // Flash left eye (pin 7) - RED - ALL LEDs including 4,5
  for(int i = 0; i < LED_COUNT_LEFT; i++) {
    leftEye.setPixelColor(i, leftEye.Color(255, 0, 0));
  }
  leftEye.show();
  delay(1000);
  
  // Test LEDs 4 and 5 specifically on left eye
  leftEye.clear();
  leftEye.setPixelColor(4, leftEye.Color(0, 255, 0)); // Green
  leftEye.setPixelColor(5, leftEye.Color(0, 255, 0)); // Green
  leftEye.show();
  Serial.println("Left eye LEDs 4,5 should be GREEN");
  delay(1000);
  leftEye.clear();
  leftEye.show();
  
  Serial.println("Testing RIGHT eye (Pin 8)...");
  // Flash right eye (pin 8) - GREEN - ALL LEDs including 4,5
  for(int i = 0; i < LED_COUNT_RIGHT; i++) {
    rightEye.setPixelColor(i, rightEye.Color(0, 255, 0));
  }
  rightEye.show();
  delay(1000);
  
  // Test LEDs 4 and 5 specifically on right eye
  rightEye.clear();
  rightEye.setPixelColor(4, rightEye.Color(255, 0, 0)); // Red
  rightEye.setPixelColor(5, rightEye.Color(255, 0, 0)); // Red
  rightEye.show();
  Serial.println("Right eye LEDs 4,5 should be RED");
  delay(1000);
  rightEye.clear();
  rightEye.show();
  
  Serial.println("Testing BOTH eyes together...");
  // Both eyes together - YELLOW
  for(int i = 0; i < 15; i++) {
    leftEye.setPixelColor(i, leftEye.Color(255, 200, 0));
    rightEye.setPixelColor(i, rightEye.Color(255, 200, 0));
  }
  leftEye.show();
  rightEye.show();
  delay(1000);
  
  Serial.println("Eye test complete!");
}

// ----------------------------------------------------------
long lastIdleTime = 0;
long lastWaveTime = 0;  // Prevent wave spam

void loop() {
  // 1. Check for Serial Commands
  if (Serial.available()) {
     String cmd = Serial.readStringUntil('\n');
     cmd.trim();
     
     if (cmd == "PHOTO") {
        photoFlash(); // LED animation + wave on photo
        return; 
     }
     else if (cmd == "LOVE") {
        emotionLove();
        delay(2000);
        lastIdleTime = millis();
        return;
     }
     else if (cmd == "SUS") {
        // Run sus animation for 3 seconds
        unsigned long susStart = millis();
        while(millis() - susStart < 3000) {
          emotionSus();
          delay(30);
        }
        lastIdleTime = millis();
        return;
     }
     else if (cmd == "WAVE") {
        Serial.println("WAVE command - Testing stepper motor");
        waveStepper();
        lastIdleTime = millis();
        return;
     }
     else if (cmd == "TEST") {
        Serial.println("TEST command - Testing all components");
        testEyes();
        delay(500);
        Serial.println("Testing motor...");
        waveStepper();
        Serial.println("Test complete!");
        return;
     }
  }

  // 2. Ultrasonic Logic - IMPROVED with multiple readings
  long readings[3];
  int validCount = 0;
  
  for(int r = 0; r < 3; r++) {
    digitalWrite(trigPin, LOW);
    delayMicroseconds(5);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(15);
    digitalWrite(trigPin, LOW);
    
    readings[r] = pulseIn(echoPin, HIGH, 50000); // Increased timeout to 50ms
    delay(10);
  }
  
  // Find median of valid readings
  long validReadings[3];
  for(int r = 0; r < 3; r++) {
    if(readings[r] > 0 && readings[r] < 25000) {
      validReadings[validCount++] = readings[r];
    }
  }
  
  if(validCount > 0) {
    // Use first valid reading (or could sort for median)
    duration = validReadings[0];
    if(validCount >= 2) {
      // Average of valid readings
      long sum = 0;
      for(int i = 0; i < validCount; i++) sum += validReadings[i];
      duration = sum / validCount;
    }
  } else {
    duration = 0;
  }

  float rawDistance;
  if (duration == 0) rawDistance = 999;
  else rawDistance = (duration * 0.0343) / 2.0;
  
  // SMOOTHING: Handle noisy 999 readings
  if (rawDistance >= 900) {
    // Got a timeout/invalid reading
    invalidReadingCount++;
    if (invalidReadingCount < MAX_INVALID_READINGS) {
      // Use last valid reading instead of 999
      distance = lastValidDistance;
      Serial.print("Dist: "); Serial.print(distance); Serial.println(" (smoothed)");
    } else {
      // Too many invalid readings, actually far away
      distance = 999;
      Serial.print("Dist: "); Serial.println(distance);
    }
  } else {
    // Got a valid reading
    distance = rawDistance;
    lastValidDistance = distance;  // Save for smoothing
    invalidReadingCount = 0;       // Reset counter
    Serial.print("Dist: "); Serial.println(distance);
  }

  // DISTANCE ZONES:
  // 0-150cm = Very close = LOVE + WAVE
  // 150-350cm = Medium = SUS (suspicious)
  // >350cm = Far = NORMAL/IDLE

  // Very close - wave and show love (0-150cm)
  if (distance > 0 && distance <= 150) {
    Serial.println(">>> LOVE MODE (0-150cm) <<<");
    emotionLove();
    
    // Only wave if not waved recently (prevent spam)
    if (millis() - lastWaveTime > 5000) {
      waveStepper();  // Stepper waves bye-bye
      lastWaveTime = millis();
    }
    
    lastIdleTime = millis();
  }
  // Medium distance - suspicious look (150-350cm)
  else if (distance > 150 && distance <= 350) {
    Serial.println(">>> SUS MODE (150-350cm) <<<");
    emotionSus();
    lastIdleTime = millis();
  }
  // Far or no object - idle animations
  else {
    if (millis() - lastIdleTime > 6000) {
       int randAnim = random(0, 5); 
       if(randAnim == 1) emotionWink();
       else if(randAnim == 2) emotionHappyBlink();
       else emotionNormal();
       
       if(randAnim != 0) { delay(1500); lastIdleTime = millis(); } 
       else { lastIdleTime = millis() - 3000; } 
    } else {
       emotionNormal();
    }
  }
  
  delay(50); 
}

// =================== PHOTO FLASH - LED CHANGES WHEN CLICKING PHOTO ===================
void photoFlash() {
  Serial.println("PHOTO MODE - Love Eyes + White Flash");
  
  // 1. Love Eyes (Hearts)
  emotionLove();
  delay(500); // Show hearts for 0.5s before flash
  
  // 2. White Flash
  for(int i = 0; i < 15; i++) {
    leftEye.setPixelColor(i, leftEye.Color(255, 255, 255));
    rightEye.setPixelColor(i, rightEye.Color(255, 255, 255));
  }
  leftEye.show();
  rightEye.show();
  delay(150); // Flash duration
  
  // 3. Back to Love Eyes briefly
  emotionLove();
  
  // 4. Wave Stepper
  waveStepper();
  
  // 5. Return to normal
  emotionNormal();
}

// =================== RAINBOW ANIMATION ===================
void emotionRainbow() {
  // Spin colors 2 times
  for(int k=0; k<256*2; k+=20) { 
     for(int i=0; i<15; i++) {
        // Pixel hue offset by position
        int pixelHue = k + (i * 65536L / 15);
        leftEye.setPixelColor(i, leftEye.gamma32(leftEye.ColorHSV(pixelHue)));
        rightEye.setPixelColor(i, rightEye.gamma32(rightEye.ColorHSV(pixelHue)));
     }
     leftEye.show();
     rightEye.show();
     delay(5);
  }
}

// =================== LOVE MODE - Pink hearts ===================
// LEFT EYE: LEDs 8,9 are white (pupil)
// RIGHT EYE: LEDs 4,5 are white (pupil)
void emotionLove() {
  // Heart shape LED indices
  int loveIdx[] = {0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14};
  uint32_t pink = leftEye.Color(255, 20, 147);
  uint32_t white = leftEye.Color(255, 255, 255);

  leftEye.clear();
  rightEye.clear();

  // Set all love LEDs
  for (int i = 0; i < sizeof(loveIdx)/sizeof(loveIdx[0]); i++) {
    int idx = loveIdx[i];
    
    // LEFT EYE: LEDs 8 and 9 are white (pupil)
    if (idx == 8 || idx == 9) {
      leftEye.setPixelColor(idx, white);
    } else {
      leftEye.setPixelColor(idx, pink);
    }
    
    // RIGHT EYE: LEDs 4 and 5 are white (pupil)
    if (idx == 4 || idx == 5) {
      rightEye.setPixelColor(idx, white);
    } else {
      rightEye.setPixelColor(idx, pink);
    }
  }
  
  leftEye.show();
  rightEye.show();
}

// =================== SUS MODE - Suspicious narrowed eyes ===================
void emotionSus() {
  // Narrowed eye LEDs (middle row only)
  int susLeds[] = {3, 4, 5, 6, 7, 8, 9, 10};
  
  // Breathing effect - slow pulse
  float val = (exp(sin(millis() / 600.0 * PI)) - 0.36787944) * 108.0; 
  int brightness = (int)val;
  if(brightness > 255) brightness = 255;
  if(brightness < 30) brightness = 30; // Minimum brightness so it's visible
  
  // Orange/amber color for suspicious look
  uint32_t susColor = leftEye.Color(brightness, (brightness * 150) / 255, 0);

  leftEye.clear();
  rightEye.clear();
  
  // Set the narrowed eye pattern on BOTH eyes
  for (int i = 0; i < 8; i++) {
    leftEye.setPixelColor(susLeds[i], susColor);
    rightEye.setPixelColor(susLeds[i], susColor);
  }
  
  leftEye.show();
  rightEye.show();
}

// =================== NORMAL MODE - Default eyes ===================
void emotionNormal() {
  leftEye.clear();
  rightEye.clear();
  
  uint32_t redDim = leftEye.Color(120, 0, 0);
  
  // Breathing effect for pupils
  float breath = (exp(sin(millis() / 800.0 * PI)) - 0.36787944) * 108.0;
  int bVal = (int)breath;
  if(bVal > 255) bVal = 255; 
  if(bVal < 10) bVal = 10;
  
  uint32_t yellowBlink = leftEye.Color(bVal, (bVal * 200) / 255, 0);

  // Outer LEDs - Static Red
  for (int i = 0; i < 15; i++) {
    if (i == 14) continue;
    if (!isInner(i)) {
      leftEye.setPixelColor(i, redDim);
      rightEye.setPixelColor(i, redDim);
    }
  }
  
  // Inner LEDs (pupils) - Breathing Yellow
  for (int i = 0; i < 4; i++) {
    leftEye.setPixelColor(innerLEDs[i], yellowBlink);
    rightEye.setPixelColor(innerLEDs[i], yellowBlink);
  }
  
  leftEye.show();
  rightEye.show();
}

// =================== WINK ANIMATION ===================
void emotionWink() {
  // Left eye closes (wink)
  leftEye.clear();
  leftEye.setPixelColor(7, leftEye.Color(100, 0, 0)); 
  leftEye.setPixelColor(8, leftEye.Color(100, 0, 0));

  // Right eye stays normal
  uint32_t redDim = rightEye.Color(120, 0, 0);
  uint32_t yellow = rightEye.Color(255, 200, 0);
  
  rightEye.clear();
  for (int i = 0; i < 15; i++) {
    if (i == 14) continue; 
    if (!isInner(i)) rightEye.setPixelColor(i, redDim);
  }
  for (int i = 0; i < 4; i++) {
    rightEye.setPixelColor(innerLEDs[i], yellow);
  }

  leftEye.show();
  rightEye.show();
}

// =================== HAPPY BLINK ===================
void emotionHappyBlink() {
  // Both eyes blink rapidly twice
  for(int j = 0; j < 2; j++) {
    leftEye.clear();
    rightEye.clear();
    leftEye.show();
    rightEye.show();
    delay(150);
    
    emotionNormal();
    delay(150);
  }
}
