int brightness = 0;  // how bright the LED is
int fadeAmount = 5;  // how many points to fade the LED by

String currentMode = "IDLE";  // Current LED mode: IDLE, PLAN, BUILD
unsigned long lastBlinkTime = 0;  // Last time LED was toggled in PLAN mode
bool ledState = false;  // Current LED state for PLAN mode

void setup() {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("READY");
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
      ledState = false;
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
  
  // Update LED based on current mode (non-blocking)
  if (currentMode == "PLAN") {
    // Blink continuously
    unsigned long now = millis();
    if (now - lastBlinkTime >= 500) {
      lastBlinkTime = now;
      ledState = !ledState;
      digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW);
    }
  } else if (currentMode == "BUILD") {
    // Stay on
    digitalWrite(LED_BUILTIN, HIGH);
  } else if (currentMode == "IDLE") {
    // Stay off
    digitalWrite(LED_BUILTIN, LOW);
  }
}
