#include <Adafruit_NeoPixel.h>

#define PIN 2	 // input pin Neopixel is attached to

#define NUMPIXELS      24 // number of neopixels in Ring

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

int delayval = 25; // timing delay

String currentMode = "IDLE";  // Current LED mode: IDLE, PLAN, BUILD
unsigned long lastBlinkTime = 0;  // Last time LED was toggled in PLAN mode

void setup() {
  pixels.begin(); // Initializes the NeoPixel library.
  Serial.begin(9600);
}

void loop() {
  // Check for serial commands
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    Serial.println("RECEIVED: [" + cmd + "]");
    
    if (cmd == "PLAN") {
      Serial.println("SWITCHING TO: PLAN");
      currentMode = "PLAN";
      lastBlinkTime = 0;
    } else if (cmd == "BUILD") {
      Serial.println("SWITCHING TO: BUILD");
      currentMode = "BUILD";
    } else if (cmd == "IDLE") {
      Serial.println("SWITCHING TO: IDLE");
      currentMode = "IDLE";
    } else {
      Serial.println("UNKNOWN: [" + cmd + "]");
    }
  }

  if (currentMode == "PLAN") {
    sweep_forward(255, 0, 255);
    sweep_backward(255, 0, 255);
  }
  else if (currentMode == "BUILD") {
    sweep_forward(0, 0, 255);
    sweep_backward(0, 0, 255);
  }
  else if (currentMode == "IDLE") {
    // Use green for debugging
    sweep_forward(0, 255, 0);
    sweep_backward(0, 255, 0);
  }
}


void sweep_forward(int r, int g, int b) {
  for(int i = 0; i < NUMPIXELS; i++){
    // pixels.Color takes RGB values, from 0,0,0 up to 255,255,255
    pixels.setPixelColor(i, pixels.Color(r, g, b));
    // set neighbouring pixels to quarter value
    if (i - 1 >= 0) {
      pixels.setPixelColor(i-1, pixels.Color(r/4, g/4, b/4));
    }
    if (i + 1 < NUMPIXELS) {
      pixels.setPixelColor(i+1, pixels.Color(r/4, g/4, b/4));
    }
    pixels.show(); // This sends the updated pixel color to the hardware.
    delay(delayval); // Delay for a period of time (in milliseconds).
  }
}

void sweep_backward(int r, int g, int b) {
  for(int i = NUMPIXELS - 1; i >= 0; i--){
    pixels.setPixelColor(i, pixels.Color(r, g, b));
    if (i - 1 >= 0) {
      pixels.setPixelColor(i-1, pixels.Color(r/4, g/4, b/4));
    }
    if (i + 1 < NUMPIXELS) {
      pixels.setPixelColor(i+1, pixels.Color(r/4, g/4, b/4));
    }
    pixels.show();
    delay(delayval);
  }
}
