#include <Adafruit_NeoPixel.h>

#define PIN 2	 // input pin Neopixel is attached to

#define NUMPIXELS      8 // number of neopixels in Ring

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

int sweepDelay = 50;
int fadeDelay = 30;
int fadeAmount = 5;
int brightness = 0;

String currentMode = "IDLE";  // Current LED mode: IDLE, PLAN, BUILD
String prevMode = "";

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
    if (cmd == "PLAN" || cmd == "BUILD" || cmd == "IDLE") {
      Serial.print("SWITCHING TO ");
      Serial.println(cmd);
      prevMode = currentMode;
      currentMode = cmd;
    }
  }

  if (currentMode == "PLAN") {
    if (prevMode != currentMode) {
      fill_solid(255, 0, 255);
    }
    sweep_forward(255, 0, 255);
    sweep_backward(255, 0, 255);
  }
  else if (currentMode == "BUILD") {
    if (prevMode != currentMode) {
      fill_solid(0, 0, 255);
    }
    sweep_forward(0, 0, 255);
    sweep_backward(0, 0, 255);
  }
  else if (currentMode == "IDLE") {
    full_fade();
  }
}

void fill_solid(int r, int g, int b) {
  for(int i = 0; i < NUMPIXELS; i++) {
    pixels.setPixelColor(i, pixels.Color(r, g, b)); 
  }
  pixels.show();
}

void full_fade() {
  brightness += fadeAmount;
  fill_solid(brightness, brightness, brightness);
  // reverse the direction of the fading at the ends of the fade:
  if (brightness <= 0 || brightness >= 255) {
    fadeAmount = -fadeAmount;
  }
  // wait to see the dimming effect
  delay(fadeDelay);
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
    delay(sweepDelay); // Delay for a period of time (in milliseconds).
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
    delay(sweepDelay);
  }
}
