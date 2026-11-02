// AYAH — Test n°1 : LED intégrée, LED blanc chaud (fondu), 3 boutons, potentiomètre.
// Câblage : voir README.md. Moniteur série à 115200 bauds.
#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

// ---- Brochage (réservé pour toute la suite du projet)
const int PIN_RGB_ONBOARD = 48;  // LED RGB intégrée (38 sur certaines cartes)
const int PIN_LED_ARCH    = 4;   // LED de test -> plus tard : éclairage de l'arche
const int PIN_BTN_PREV    = 6;
const int PIN_BTN_PLAY    = 7;
const int PIN_BTN_NEXT    = 8;
const int PIN_POT         = 1;   // curseur du potentiomètre (extrémités sur 3V3 et GND !)
const int PIN_STRIP       = 5;   // DIN du ruban adressable (via résistance 330 Ω)

// ---- Ruban LED : on limite volontairement le nombre de LED et la puissance (alim USB)
const int   STRIP_LEDS    = 10;
const float STRIP_MAX     = 0.40f;          // 40 % max tant qu'on est alimenté par l'USB
Adafruit_NeoPixel strip(STRIP_LEDS, PIN_STRIP, NEO_GRB + NEO_KHZ800);

// ---- État du « lecteur » simulé
int  surah   = 1;      // 1..114
bool playing = false;
int  volume  = 0;      // 0..21 (échelle de la future bibliothèque audio)

// ---- Bouton avec anti-rebond et appui long
struct Button {
  int pin; bool last = HIGH; uint32_t changedAt = 0, pressedAt = 0; bool longDone = false;
};
Button bPrev{PIN_BTN_PREV}, bPlay{PIN_BTN_PLAY}, bNext{PIN_BTN_NEXT};

// Renvoie 1 = appui court (au relâchement), 2 = appui long (> 600 ms), 0 = rien
int readButton(Button &b) {
  bool s = digitalRead(b.pin);
  uint32_t now = millis();
  if (s != b.last && now - b.changedAt > 25) {
    b.changedAt = now; b.last = s;
    if (s == LOW) { b.pressedAt = now; b.longDone = false; }
    else if (!b.longDone) return 1;
  }
  if (s == LOW && !b.longDone && now - b.pressedAt > 600) { b.longDone = true; return 2; }
  return 0;
}

// ---- LED : PWM 12 bits à 20 kHz (inaudible, sans scintillement) + correction gamma
void ledInit() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_LED_ARCH, 20000, 12);
#else
  ledcSetup(0, 20000, 12); ledcAttachPin(PIN_LED_ARCH, 0);
#endif
}
void ledSet(float level) {               // level 0.0 .. 1.0 (perçu)
  uint32_t duty = (uint32_t)(powf(constrain(level, 0.f, 1.f), 2.2f) * 4095);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(PIN_LED_ARCH, duty);
#else
  ledcWrite(0, duty);
#endif
}
void onboard(uint8_t r, uint8_t g, uint8_t b) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  rgbLedWrite(PIN_RGB_ONBOARD, r, g, b);
#else
  neopixelWrite(PIN_RGB_ONBOARD, r, g, b);
#endif
}

// Blanc chaud ~2700 K obtenu en RGB (R fort, G moyen, B très faible)
void stripSet(float level) {
  float k = powf(constrain(level, 0.f, 1.f), 2.2f) * STRIP_MAX;
  for (int i = 0; i < STRIP_LEDS; i++) strip.setPixelColor(i, strip.Color(255 * k, 130 * k, 35 * k));
  strip.show();
}

void printState() {
  Serial.printf("%s  Sourate %03d / 114   volume %2d\n", playing ? "▶" : "⏸", surah, volume);
}

void setup() {
  Serial.begin(115200);
  delay(300);
  pinMode(PIN_BTN_PREV, INPUT_PULLUP);
  pinMode(PIN_BTN_PLAY, INPUT_PULLUP);
  pinMode(PIN_BTN_NEXT, INPUT_PULLUP);
  analogReadResolution(12);
  ledInit();
  strip.begin();
  strip.clear();
  strip.show();
  Serial.printf("\nAYAH test n°1 — PSRAM : %u Ko, flash : %u Mo\n",
                ESP.getPsramSize() / 1024, ESP.getFlashChipSize() / (1024 * 1024));
  // Animation de démarrage : montée douce de la lumière
  for (int i = 0; i <= 100; i++) { ledSet(i / 100.f * 0.6f); stripSet(i / 100.f * 0.6f); onboard(i / 4, i / 8, i / 40); delay(12); }
  printState();
}

void loop() {
  // Boutons : court = action, long sur PLAY = mode nuit
  static bool night = false;
  int p = readButton(bPrev), y = readButton(bPlay), n = readButton(bNext);
  if (p == 1) { surah = surah == 1 ? 114 : surah - 1; printState(); }
  if (n == 1) { surah = surah == 114 ? 1 : surah + 1; printState(); }
  if (p == 2) { surah = max(1, surah - 10); printState(); }      // appui long = saut de 10
  if (n == 2) { surah = min(114, surah + 10); printState(); }
  if (y == 1) { playing = !playing; printState(); }
  if (y == 2) { night = !night; Serial.println(night ? "Mode nuit ON" : "Mode nuit OFF"); }

  // Potentiomètre -> volume 0..21 (moyenne glissante pour éviter le bruit)
  static float pot = analogRead(PIN_POT);
  pot = pot * 0.9f + analogRead(PIN_POT) * 0.1f;
  int v = map((int)pot, 0, 4095, 0, 21);
  if (abs(v - volume) >= 1) { volume = v; printState(); }

  // Lumière : respiration douce en lecture, fixe à l'arrêt, très faible en mode nuit
  float base = night ? 0.08f : 0.6f;
  float level = playing ? base * (0.75f + 0.25f * sinf(millis() / 900.f)) : base;
  ledSet(level);
  static uint32_t lastStrip = 0;          // le ruban n'a pas besoin de 200 rafraîchissements/s
  if (millis() - lastStrip > 20) { lastStrip = millis(); stripSet(level); }
  onboard(playing ? 40 : 12, playing ? 20 : 6, 2);
  delay(5);
}
