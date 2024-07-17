#include <SPI.h>
#include <WiFi.h>
#include <Arduino.h>
#include <MFRC522.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <LiquidCrystal_I2C.h>

/*
 // Pin Layout for RC522
  * RST_PIN:      PIN 4
  * SDA_PIN:      PIN 5
  * SCK_PIN:      PIN 18
  * MOSI_PIN:     PIN 23
  * MISO_PIN:     PIN 19
  
  // Pin Layout for LCD
  * VCC:         5V
  * SDA:         21
  * SCL:         22
 */

const char* ssid = "OK-ALI";
const char* password = "@/^@&^/@";
String url = "http://192.168.70.3:8000/";
#define RST_PIN 4
#define SS_PIN 5
MFRC522 mfrc522(SS_PIN, RST_PIN);
MFRC522::MIFARE_Key key;
LiquidCrystal_I2C lcd(0x27, 16, 2);

int writeBlock(int blockNumber, byte arrayAddress[]);
int readBlock(int blockNumber, byte arrayAddress[]);
void printHex(byte *buffer, byte bufferSize);
String getData(int);
byte setData(String, String, String, String);
int basic(byte);
byte prev_op = 0;
String prev_n = "not-set";

void setup() {
  Serial.begin(115200);
  SPI.begin();
  WiFi.begin(ssid, password);
  Serial.print("Connecting to the WiFi ");
  for (byte i=0; i<10; i++) {
    if (WiFi.status() != WL_CONNECTED) {
      delay(1000);
      Serial.print(".");
    }
    else {
      Serial.println();
      Serial.print("Connected to WiFi: ");
      Serial.println(ssid);
      mfrc522.PCD_Init();
      for (byte i = 0; i < 6; i++) {
              key.keyByte[i] = 0xFF;
      }
      lcd.init();                       // Initialize the LCD
      lcd.backlight();                  // Turn on the backlight
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Scan Your Card");
      HTTPClient http;
      http.begin(url+"reset");
      int httpCode = http.GET();
      if (httpCode != 200)
        Serial.println("[C]    Server Reset Failed");
      http.end();
      return;
    }
  }
  Serial.println();
  Serial.println("[C] => Wifi Connection Failed ...");
}

void loop() {
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  mfrc522.PCD_Init();
  if ((WiFi.status() == WL_CONNECTED)) {
    HTTPClient http;
    http.begin(url);
    int httpCode = http.GET();
    if (httpCode == 200) {
      String payload = http.getString();
      http.end();
      Serial.println("[I]    Received payload:");
      Serial.print("[D]    ");
      Serial.println(payload);
      
      DynamicJsonDocument doc(1024);
      DeserializationError error = deserializeJson(doc, payload);

      if (error) {
        Serial.print("[E]    deserializeJson() failed: ");
        Serial.println(error.f_str());
        return;
      }
      
      int option = doc["option"];
      String n = doc["name"];
      Serial.print("[I]    Current Option: ");
      Serial.println(option);
      // doc.clear();
      if (option == 6 || option == 7) {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Scan to Register");
        String t = doc["type"];
        String e = doc["extra"];
        String i = doc["id"];
        doc.clear();
        byte code = setData(t, n, e, i);
        if (code==1)
          return;
        else if (code==2) {
          Serial.println("[E]    Error in writing data");
          lcd.clear();
          lcd.setCursor(0, 0);
          lcd.print("Error in Writing");
          lcd.setCursor(0, 1);
          lcd.print("Resetting in 2s ");
        }
        delay(2000);
        mfrc522.PICC_HaltA();
        mfrc522.PCD_StopCrypto1();
        esp_restart();
      }
      else if ((prev_op != option)||(prev_n != n)) {
        prev_op = option;
        prev_n = n;
        if (option != 0) {
          switch (option) {
            case 1: // card required first
              Serial.println("[I]    Scan your Card First");
              lcd.clear();
              lcd.setCursor(0, 0);
              lcd.print("Scan Your Card");
              lcd.setCursor(0, 1);
              lcd.print("Login First...!");
              if (basic(1))
                return;
              break;
            case 2: // Logged In
              lcd.clear();
              lcd.setCursor(0, 0);
              lcd.print("[I] Logged In");
              lcd.setCursor(0, 1);
              lcd.print(n);
              if (basic(2))
                return;
              break;
            case 3:
              Serial.println("[C]    LogOut First from chat");
              lcd.clear();
              lcd.setCursor(0, 0);
              lcd.print("LogOut First...!");
              if (basic(3))
                return;
              break;
            case 4:
              Serial.println("[I]    Book Borrowed");
              lcd.clear();
              lcd.setCursor(0, 0);
              lcd.print("[I]Book Borrowed");
              lcd.setCursor(0, 1);
              lcd.print(n);
              if (basic(4))
                return;
              break;
            case 5:
              Serial.println("[I]    Logging Out");
              mfrc522.PICC_HaltA();
              mfrc522.PCD_StopCrypto1();
              esp_restart();
              break;
            case 8:
              Serial.println("[I]    Book Returned");
              lcd.clear();
              lcd.setCursor(0, 0);
              lcd.print("[I]Book Returned");
              lcd.setCursor(0, 1);
              lcd.print(n);
              if (basic(8))
                return;
              break;
            default:
              Serial.println("[E]    Invalid Option from Server");
          }
        }
        else {
          lcd.clear();
          lcd.setCursor(0, 0);
          lcd.print("Scan Your Card");
          if (basic(0)) // basic returns 1 when error or no card is present
            return;
        }
      }
      else {
        if (basic(prev_op)) // basic returns 1 when error or no card is present
            return;
      }
      doc.clear();
    }
    else {
      http.end();
      Serial.print("[E]    httoCode: ");
      Serial.println(httpCode);
      Serial.println("[E]    HTTP GET '/' not successful");
    }
  }
  else {
    Serial.println("[E]    WiFi not connected");
    WiFi.begin(ssid, password);
    Serial.print("Connecting to the WiFi ");
    for (byte i=0; i<10; i++) {
      if (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
      }
      else {
        Serial.println();
        Serial.print("Connected to WiFi: ");
        Serial.println(ssid);
        return;
      }
    }
  }
  
  delay(200);
  Serial.println("[I]    Done for this time");
}


// Functions Implementation
int writeBlock(int blockNumber, byte arrayAddress[]) 
{
  //this makes sure that we only write into data blocks. Every 4th block is a trailer block for the access/security info.
  int largestModulo4Number=blockNumber/4*4;
  int trailerBlock=largestModulo4Number+3;//determine trailer block for the sector
  if (blockNumber > 2 && (blockNumber+1)%4 == 0){Serial.print(blockNumber);Serial.println(" is a trailer block:");return 2;}//block number is a trailer block (modulo 4); quit and send error code 2
  Serial.print("[I]    ");
  Serial.print(blockNumber);
  Serial.println(" is a data block:");
  
  /*****************************************authentication of the desired block for access***********************************************************/
  MFRC522::StatusCode status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerBlock, &key, &(mfrc522.uid));
  //byte PCD_Authenticate(byte command, byte blockAddr, MIFARE_Key *key, Uid *uid);
  //this method is used to authenticate a certain block for writing or reading
  //command: See enumerations above -> PICC_CMD_MF_AUTH_KEY_A = 0x60 (=1100000),    // this command performs authentication with Key A
  //blockAddr is the number of the block from 0 to 15.
  //MIFARE_Key *key is a pointer to the MIFARE_Key struct defined above, this struct needs to be defined for each block. New cards have all A/B= FF FF FF FF FF FF
  //Uid *uid is a pointer to the UID struct that contains the user ID of the card.
  if (status != MFRC522::STATUS_OK) {
         Serial.print("[E]    PCD_Authenticate() failed: ");
         Serial.println(mfrc522.GetStatusCodeName(status));
         return 3;//return "3" as error message
  }
  //it appears the authentication needs to be made before every block read/write within a specific sector.
  //If a different sector is being authenticated access to the previous one is lost.


  /*****************************************writing the block***********************************************************/
        
  status = mfrc522.MIFARE_Write(blockNumber, arrayAddress, 16);//valueBlockA is the block number, MIFARE_Write(block number (0-15), byte array containing 16 values, number of bytes in block (=16))
  //status = mfrc522.MIFARE_Write(9, value1Block, 16);
  if (status != MFRC522::STATUS_OK) {
           Serial.print("[E]    MIFARE_Write() failed: ");
           Serial.println(mfrc522.GetStatusCodeName(status));
           return 4;//return "4" as error message
  }
  Serial.println("[I]    block was written");

  return 0;
}

int readBlock(int blockNumber, byte arrayAddress[]) 
{
  int largestModulo4Number=blockNumber/4*4;
  int trailerBlock=largestModulo4Number+3;//determine trailer block for the sector

  /*****************************************authentication of the desired block for access***********************************************************/
  MFRC522::StatusCode status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerBlock, &key, &(mfrc522.uid));
  //byte PCD_Authenticate(byte command, byte blockAddr, MIFARE_Key *key, Uid *uid);
  //this method is used to authenticate a certain block for writing or reading
  //command: See enumerations above -> PICC_CMD_MF_AUTH_KEY_A = 0x60 (=1100000),    // this command performs authentication with Key A
  //blockAddr is the number of the block from 0 to 15.
  //MIFARE_Key *key is a pointer to the MIFARE_Key struct defined above, this struct needs to be defined for each block. New cards have all A/B= FF FF FF FF FF FF
  //Uid *uid is a pointer to the UID struct that contains the user ID of the card.
  if (status != MFRC522::STATUS_OK) {
         Serial.print("[E]    PCD_Authenticate() failed (read): ");
         Serial.println(mfrc522.GetStatusCodeName(status));
         return 3;//return "3" as error message
  }
  //it appears the authentication needs to be made before every block read/write within a specific sector.
  //If a different sector is being authenticated access to the previous one is lost.


  /*****************************************reading a block***********************************************************/
        
  byte buffersize = 18;//we need to define a variable with the read buffer size, since the MIFARE_Read method below needs a pointer to the variable that contains the size... 
  status = mfrc522.MIFARE_Read(blockNumber, arrayAddress, &buffersize);//&buffersize is a pointer to the buffersize variable; MIFARE_Read requires a pointer instead of just a number
  if (status != MFRC522::STATUS_OK) {
          Serial.print("[E]    MIFARE_read() failed: ");
          Serial.println((const char*)mfrc522.GetStatusCodeName(status));
          return 4;//return "4" as error message
  }
  Serial.println("[I]    block was read");

  return 0;
}

void printHex(byte *buffer, byte bufferSize) {
  for (byte i = 0; i < bufferSize; i++) {
    Serial.print(buffer[i] < 0x10 ? " 0" : " ");
    Serial.print(buffer[i], HEX);
  }
}

String getData(int block) {
  byte readbackblock[18];
  readBlock(block, readbackblock); 
  String readbackblockString = "";

  for (int i = 0; i < 16; i++) {
    readbackblockString += (char)readbackblock[i];
  }
  return readbackblockString;
}

byte convertAndFeed(byte block, String inp) {
  byte data[16];
  for (byte i = 0; i < 16; i++)
    data[i] = (byte)inp[i];
  if (writeBlock(block, data))
    return 2;
  return 0;
}

byte setData(String type, String name, String extra, String id) {
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return 1;
  }
  Serial.println("[I]    New Card Present OK");

  if (!mfrc522.PICC_ReadCardSerial()) {
    Serial.println("[E]    Read Card Serial not OK");
    return 1;
  }
  Serial.println("[I]    Read Card Serial OK");
  
  Serial.print(F("[I]    The NUID tag is: 0x"));
  printHex(mfrc522.uid.uidByte, mfrc522.uid.size);
  Serial.println("");

  
  if (convertAndFeed(1, type))
    return 2;
  if (convertAndFeed(2, name))
    return 2;
  if (convertAndFeed(4, extra))
    return 2;
  if (convertAndFeed(5, id))
    return 2;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(type);
  lcd.setCursor(0, 1);
  lcd.print("Reg Success");
  return 0;
}

int basic(byte v) {
  // read card
  if (!mfrc522.PICC_IsNewCardPresent())
    return 1;

  Serial.println("[I]    New Card Present OK");

  if (!mfrc522.PICC_ReadCardSerial()) {
    Serial.println("[E]    Read Card Serial not OK");
    return 1;
  }
  Serial.println("[I]    Read Card Serial OK");

  Serial.print(F("[I]    The NUID tag is: 0x"));
  printHex(mfrc522.uid.uidByte, mfrc522.uid.size);
  Serial.println("");
  String data;
  DynamicJsonDocument doc(1024);
  data = getData(1); // type
  doc["type"] = data;
  data = getData(2); // name
  doc["name"] = data;
  if (v == 2) {
    Serial.print("[I]   ");
    Serial.print(data);
    Serial.println(" is logged in");
  }
  data = getData(4); // author, dept
  doc["extra"] = data;
  data = getData(5); // isbn, id
  doc["id"] = data;

  serializeJson(doc, data);
  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  byte httpCode = http.POST(data);
  http.end();
  if (httpCode == 200)
    Serial.println("[I]    Data sent successfully");

  else {
    Serial.println("[E]    HTTP POST '/' not successful");
    return 1;
  }

  return 0;
}
