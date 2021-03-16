import numpy as np
from mss import mss
from PIL import Image
import cv2
import time
import signal
import sys
#import pyautogui
import copy
import uinput
from shapely import geometry


from pynput.keyboard import Key, Controller as KeyboardController
from pynput.keyboard import Listener
from pynput.mouse import Button, Controller as MouseController

import copy
mouse = MouseController()
keyboard = KeyboardController()
    

contagemTiros = 0

zona_morta = []	# [linha, posicao, tempo]

TEMPO_DE_ESPERA_ENTRE_OS_TIROS = 0.01
TEMPO_DE_ESPERA_ENTRE_RECARREGAMENTO = 2.25
MUNICAO = 7
offsetX = 41
offsetY = 613

halt = False



def on_release(key):
	pass

def on_press(key):
	global halt, TEMPO_DE_ESPERA_ENTRE_OS_TIROS, MUNICAO

	if key == Key.enter:

		if halt == False:
			halt = True
		else:
			halt = False

	if 'char' in dir(key):
		if key.char == 'o':
			TEMPO_DE_ESPERA_ENTRE_OS_TIROS += 0.0005
			print("Tempo entre os tiros: ")
			print(TEMPO_DE_ESPERA_ENTRE_OS_TIROS)
			

		if key.char == 'l':
			TEMPO_DE_ESPERA_ENTRE_OS_TIROS -= 0.0005
			print("Tempo entre os tiros: ")
			print(TEMPO_DE_ESPERA_ENTRE_OS_TIROS)

		if key.char == 'i':
			MUNICAO += 1
			print("MUNICAO: ")
			print(MUNICAO)
			

		if key.char == 'k':
			MUNICAO -= 1
			print("Tempo MUNICAO os tiros: ")
			print(MUNICAO)



		

def capture():
	with mss() as sct:
			monitor = sct.monitors[0]
			img = np.array(sct.grab(monitor))

			return img

def showArray(img):

	cv2.imshow('frame', img)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		exit()


# !!! PUSH ctr IF THINGS GOING WRONG !!! (useless)
def panic_button(sig, frame):
    print('falous')
    sys.exit(0)									

def verificaLinha(img, anterior, linha):

	mouseY = linha[1]
	linha = linha[0]

	
	showArray(img)


	#mouseY = 170
	if 255 in linha:
		
		ocorrencias = np.where(linha == 255)[0]
		mouseX = ocorrencias[ocorrencias.shape[0]-1]
		#print("encontrou uma linha preta na posicao: " + str(mouseX) + ", " + str(mouseY))
		#print(linha1)

		if mouseX == anterior:
			print("Não vamos clicar")
			return mouseX

		mouse.position = (offsetX + mouseX + 2, offsetY + mouseY)
		mouse.click(Button.left)


		return mouseX	


def processImage(img, cont, anterior):

	h, w, c = img.shape
	
	# Vamos cortar a imagem na área que nos interessa
	img = img[offsetY: (offsetY+620), offsetX: (offsetX+1162), 0:4]	

	# Vamos retirar a parte transparente da imagem
	img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB) # RGBA to RGB

	# Transformar em tons de cinza
	img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	# Vamos obter somente o canal verde da imagem
	#img = img[:,:,1]

	ret, img = cv2.threshold(img,27,255,cv2.THRESH_BINARY_INV)



	return img

def get_rect(x, y, width, height, angle, img):
    
    img[x-35:x+35, y-35:y+35] = 255

def verificaZonaMorta(linha, posX, img):
	for item in zona_morta:
		
		if item[0] == linha and item[1] - 60 < posX and item[1] + 60 > posX: # and posX < 750:
			return True

	return False


def insereZonaMorta(linha, posX, tempo):
	zona_morta.append([linha, posX, tempo])


def atualizaZonaMorta():
	for index, item in enumerate(zona_morta):
		# Se já faz mais de 2 segundos que este cadaver está na zona morta, tira ele daí
		if item[2] + 1 < time.time():
			del zona_morta[index]

 # Retorna a posição X e Y do alvo mais a frente
def bonecoMaisAdiante(img):	

	global contagemTiros, MUNICAO

	linhas = escolheLinha(img)

	lenY = img.shape[0]
	lenX = img.shape[1]

	posX = -1
	posY = -1
	linha = -1

	index = 0
	aux = 0
	for linha_item in linhas:
		# Os valores 255 serão os primeiros
		for index, item in enumerate(reversed(linha_item[0])):
			if item == 255:
				posX = lenX - index
				posY = linha_item[1]
				if not verificaZonaMorta(linha_item[1], posX, img):

					if True: #aux == 0:
						mira(posX, posY)
						clica()
						desMira()		
						aux = 1
						insereZonaMorta(linha_item[1], posX, time.time())

						contagemTiros += 1

						if contagemTiros == MUNICAO:
							recarrega()
							atualizaZonaMorta()
							contagemTiros = 0
							return

						time.sleep(TEMPO_DE_ESPERA_ENTRE_OS_TIROS)		

						break	# Atira no primeito boneco da linha e depois muda				
			else:
				aux = 0


	atualizaZonaMorta()

	return
	"""
		if 255 in linha_item[0]:

			ocorrencias = np.where(linha_item[0] == 255)[0]
			pos = ocorrencias[ocorrencias.shape[0]-1]
			if pos > posX and not verificaZonaMorta(linha_item[1], pos, img):
				posX = pos
				posY = linha_item[1]
				linha = linha_item[1]
			
	

	atualizaZonaMorta()
	if posX > -1:
		linhaVertical = img[:,posX-2]
		ocorrencias = np.where(linhaVertical == 255)[0]
		if len(ocorrencias)== 0:
			print("kkkk")
			return [-1, -1]

		pos = ocorrencias[0]	
		posY = pos+5
		insereZonaMorta(linha, posX, time.time())

	return [posX, posY]
	"""
	

def escolheLinha(img):

	linhas = []

	linha0 = img[0, :]
	linhas.append([linha0, 0])
	linha0 = img[1, :]
	linhas.append([linha0, 1])	

	linha1 = img[60, :]
	linhas.append([linha1, 60])
	linha2 = img[61, :]
	linhas.append([linha1, 61])	

	
	linha2 = img[110, :]
	linhas.append([linha2, 110])
	linha2 = img[111, :]
	linhas.append([linha2, 111])	

	linha5 = img[156, :]
	linhas.append([linha5, 156])
	linha5 = img[157, :]
	linhas.append([linha5, 157])	


	linha9 = img[200, :]
	linhas.append([linha9, 200])
	linha9 = img[201, :]
	linhas.append([linha9, 201])	

	return linhas

def mira(mouseX, mouseY):
	mouse.position = (offsetX + mouseX, offsetY + mouseY)

def desMira():
	mouse.position = (300,300)

def clica():

	mouse.click(Button.left)	


def recarrega():
	print("pressionando espaço")
	keyboard.press(Key.space)
	time.sleep(TEMPO_DE_ESPERA_ENTRE_RECARREGAMENTO)
	keyboard.release(Key.space)

def main():
	# Bora

	global halt, MUNICAO, TEMPO_DE_ESPERA_ENTRE_OS_TIROS

	listener = Listener(on_press=on_press, on_release=on_release)
	listener.start()

	kernel = np.ones((5,5),np.uint8)
	time.sleep(2)

	anterior = -1
	cont = 0
	cont2 = 0

	linhas = []

	start = time.time()
	
	while 1:

		if halt == True:
			print('Halted')
			time.sleep(0.1)
			continue

		#for i in range(12):

		img = capture()	
		img = processImage(img, cont, anterior)
		#img = cv2.erode(img,kernel,iterations = 1)
		#img = cv2.dilate(img,kernel,iterations = 1)

		#linhas = escolheLinha(img, linhas)
		#posX, posY = bonecoMaisAdiante(img)	
		bonecoMaisAdiante(img)	
		showArray(img)


		continue

		cont2 += 1

		if cont2 == 100:			
			print("Tempo percorrido: " + str( (time.time() - start) / cont2))
			start = time.time()
			cont2 = 0

		if posX > -1:
			mira(posX, posY)
			clica()
			desMira()
			time.sleep(TEMPO_DE_ESPERA_ENTRE_OS_TIROS)

			cont += 1

		if cont > MUNICAO:
			recarrega()
			cont = 0


		
		#anterior = verificaLinha(img, anterior, [img[45, :], 45])




if __name__ == '__main__':
	signal.signal(signal.SIGINT, panic_button)
	main()
