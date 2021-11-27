# -*- coding: utf-8 -*-
"""RC4 encryption.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1G-rM9wVNLaLmlqhKDN7RMvB5bwagWUjF

# **Cracking RC4**
"""

import csv

"""## Helper Functions"""

#Swap values of two indexes in the State Array
def swapValuesStateArray(stateArr, i, j):
  temp = stateArr[i]
  stateArr[i] = stateArr[j]
  stateArr[j] = temp

#Initialse the State Array
def initSA(stateArr):
  if len(stateArr) == 0:
    for i in range(256):
      stateArr.append(i)

  else:            #reset the State Array if there already is elements in it
    for i in range(256):
      stateArr[i] = i

#Key Scheduling Algorithm (KSA)
def ksa(key, stateArr):
  j = 0
  for i in range(256):
    j = (j + stateArr[i] + ord(key[i % len(key)])) % 256 #ord returns unicode 
    swapValuesStateArray(stateArr, i, j)

# KSA for key whose value is int
def ksaInt(key, stateArr):
    j = 0
    for i in range(256):
        j = (j + stateArr[i] + key[i % len(key)]) % 256
        swapValuesStateArray(stateArr, i, j)

#Pseudo Random Generator Algorithm (PRGA) for one byte of key stream
def prga(stateArr, i, j):
  i = (i + 1) % 256 
  j = (j + stateArr[i]) % 256
  swapValuesStateArray(stateArr, i, j)
  keyStreamByte = stateArr[(stateArr[i] + stateArr[j]) % 256]
  return keyStreamByte

#Pseudo Random Generator Algorithm (PRGA) for full plain text length of key stream
def prgaFull(plainText, stateArr):
  i = 0
  j = 0
  keyStream = ""
  #have to generate a key stream as long as the plain text
  for i in range(len(plainText)):
    keyStreamByte = prga(stateArr, i, j)
    keyStream += chr(keyStreamByte) #chr return string that represents char that's linked to unicode
  return keyStream

def rc4_encrypt(WEP_key, plain_text):
  stateArr = []
  enc_keyStream = ""
  enc_plainText = ""
  dec_keyStream = ""
  dec_plainText = ""

  #Encryption
  initSA(stateArr)
  ksa(WEP_key, stateArr)
  enc_keyStream = prgaFull(plain_text, stateArr)
  for i in range(len(plain_text)):
      enc_plainText += chr(ord(plain_text[i]) ^ ord(enc_keyStream[i]))
  print("encryption: " + enc_plainText)
  return enc_plainText

def rc4_decrypt(WEP_key, enc_plainText):
  stateArr = []
  dec_keyStream = ""
  dec_plainText = ""

  initSA(stateArr)
  ksa(WEP_key, stateArr)
  dec_keyStream = prgaFull(enc_plainText, stateArr)
  for i in range(len(enc_plainText)):
      dec_plainText += chr(ord(enc_plainText[i]) ^ ord(dec_keyStream[i]))
  print("decryption: " + dec_plainText)
  return dec_plainText

def generate_key_packets(WEP_key):

  # Clear out what is originally in the file.
  WEPOutputSim = open("WEPOutputSim.csv", "w").close()
  # Append possible IV and keyStreamByte.
  WEPOutputSim = open("WEPOutputSim.csv", "a")
  WEPOutputSim.write("IV0,IV1,IV2,Snapheader\n")

  key = []
  i=0
  while i < len(WEP_key):
    #retrieve each byte of keys(2 characters) and convert to int
    keyByte = int(WEP_key[i] + WEP_key[i+1], 16)
    key.append(keyByte) 
    i += 2

  # Initial IV form
  IV = [3, 255, 0]
  sessionKey = IV + key
  SNAPheader = "aa"

  # A is the number of known key bytes, starts from 0 to the length of key.
  for A in range(len(key)):
    #increase IV's first byte from 0 to length of key
    #[3,255,0,a,b,c,d] ... -> [3,255,255,a,b,c,d] ... -> [4,255,0,a,b,c,d]
    IV[0] = A + 3

    #increase IV's third byte from 0 to 255
    #[3,255,0,a,b,c,d]
    #[3,255,1,a,b,c,d]
    for i in range(256):
      IV[2] = i
      sessionKey = IV + key

      stateArr = []
      initSA(stateArr)
      ksaInt(sessionKey, stateArr)
      i = 0
      j = 0
      keyStreamByte = prga(stateArr, i, j)

      #encrypt SNAPheader with keyStreamByte
      cipherByte = int(SNAPheader, 16) ^ keyStreamByte
      WEPOutputSim.write(str(IV[0]) + "," + str(IV[1]) + "," + str(IV[2]) + "," + str(cipherByte) + "\n")
  print("WEPOutputSim.csv is generated sucessfully.")

def retrieve_key():
  rows = []
  stateArr = []
  SNAPheader = "aa"
  with open("WEPOutputSim.csv") as csvfile:
    reader = csv.reader(csvfile) # change contents to floats
    next(reader, None)  # skip the headers
    for row in reader: # each row is a list
        rows.append(row)
        
  keyLength = int(rows[-1][0]) - 3 + 1
  print("keyLength is: " + str(keyLength))

  #initialize key to [0, 0, 0]
  WEP_key = [0] * 3

  #This for loop recovers each byte of the key, and append the next byte to WEP_key
  #A is the index of the current byte of key we are working on in this iteration of the loop
  for A in range(keyLength):
      #initialize prob array to all 0, the highest probability in the end will be selected as the byte[A] of pre-shared key
      prob = [0] * 256
      #Looping through the simulated packets
      for row in rows:
          #reproduce the first 3 columns of simulated packets
          WEP_key[0] = int(row[0])
          WEP_key[1] = int(row[1])
          WEP_key[2] = int(row[2])

          #initialize KSA
          j = 0
          initSA(stateArr)
          # Simulate the S-Box after KSA initialization.
          #For loop for each byte of the key
          for i in range(A + 3):
              j = (j + stateArr[i] + WEP_key[i]) % 256
              swapValuesStateArray(stateArr, i, j)

          i = A + 3
          #z is the first element of the completed stateArr
          z = stateArr[0]
          # if resolved condition is possibly met.
          if z == A + 3:
              #XOR the known SNAPheader('AA') with the encrypted 'AA' to get the corresponding byte in keystream
              keyStreamByte = int(row[3]) ^ int(SNAPheader, 16)
              #retrieve the key byte
              keyByte = (keyStreamByte - j - stateArr[i]) % 256
              prob[keyByte] += 1
      # Assume that the most hit is the correct password.
      highestProbability = prob.index(max(prob))
      WEP_key.append(highestProbability)

  # Get rid of first 24-bit initialization vector.
  userInput = WEP_key[3:]
  result = [format(WEP_key, 'x') for WEP_key in userInput]
  rawkey = ''.join(result).upper()
  print(rawkey)
  return rawkey
