from multiprocessing import Process, Manager, BoundedSemaphore, Semaphore, Lock, current_process, Value, Array
from random import random

class practica1():
	#@pre : K, N, NPROD > 0 enteros
	def __init__(self, NPROD, N, K = 1):
		self.K	   = K #Longitud de la cola de cada productor, si queremos que no tenga cola, K = 1 (opción por defecto)
		self.N	   = N #Cantidad total a producir por cada productor
		self.NPROD = NPROD #Numero de productores
		
		self.manager    = Manager()
		self.almacen    = self.manager.list() #Lista para almacenar los datos ordenados
		self.storage    = Array('i', NPROD) #Lista para almacenar el primero de cada productor (el que está visible para el consumidor)
		for i in range(NPROD):
			self.storage[i] = -2
		self.colas      = [Array('i', K) for i in range(NPROD)] #Colas de los productores, para almacenar el resto de productos (a parte del visible para el consumidor)
		self.index      = [Value('i', 0) for i in range(NPROD)] #Posición de la lista que usamos de cola por la que va almacenando cada productor
		self.indexLee   = [Value('i', 0) for i in range(NPROD)] #Posición de la lista que usamos de cola por la que va leyendo cada productor
		self.occStorage = Value('i', 0) #Cantidad de posiciones del storage ocupadas

		self.empty	        = [BoundedSemaphore(K) for i in range(NPROD)] #Semaforo para controlar que los productores no hagan más de lo que cabe en la cola
		self.colaEnUso	    = [BoundedSemaphore(1) for i in range(NPROD)] #Semaforo para controlar que los productores no cambien la cola al mismo tiempo que el consumidor
		self.storageLibre   = Lock() #Lock para controlar que el storage no está siendo usado por otros procesos
		self.storageNoVacio = Lock() #Lock para controlar que el consumidor no empiece a consumir hasta que el storage esté ocupado
		self.storageNoVacio.acquire() #El storage empieza vacío por lo que bloqueamos el Lock para que el consumidor espera a que se llene
		
	#Comprueba si hay un dato en la cola de pid para meter en storage
	def cambiaStorage(self, pid):
		with self.storageLibre:
			if self.storage[pid] == -2:
				self.storage[pid] = self.colas[pid][self.indexLee[pid].value]
				self.occStorage.value += 1
				if self.occStorage.value == self.NPROD:
					print("Listos para ser consumidos")
					self.storageNoVacio.release() #Ya se ha llenado el storage, por lo que liberamos el Lock

	#Añade dato a la cola pid
	def addDato(self, dato, pid):
		self.empty[pid].acquire() #Comprobamos que no está llena la cola
		with self.colaEnUso[pid]: #Comprobamos que el consumidor no está usando la cola
			self.colas[pid][self.index[pid].value] = dato #Añadimos el dato a la cola
			self.cambiaStorage(pid)
			self.index[pid].value += 1
			if self.index[pid].value >= self.K:
				self.index[pid].value = 0

	#Devuelve el primer dato de la cola pid
	def getDato(self, pid):
		with self.colaEnUso[pid]: #Comprobamos que el productor no está usando la cola
			dato = self.colas[pid][self.indexLee[pid].value] 
			self.occStorage.value -= 1
			self.indexLee[pid].value += 1
			if self.indexLee[pid].value >= self.K:
				self.indexLee[pid].value = 0
			self.storage[pid] = -2
			self.cambiaStorage(pid)
		self.empty[pid].release()
		return dato
				
	#Añade el menor de los datos del storage al almacen
	def merge(self):
		dato, mi = self.storage[0], 0 #Buscamos el mínimo de storage (No cogemos el lock de storage, por que por la forma en que está definido, una vez se ha llenado no lo van a modificar otros)
		for p in range(1, self.NPROD):
			if self.storage[p] != -1 and (dato == -1 or dato >= self.storage[p]): #Ignoramos los productores que ya han terminado de producir y nos quedamos con el menor dato
				mi, dato = p, self.storage[p]
		self.almacen.append(self.getDato(mi))
		print (f"consumer almacenado {dato}")

	#Proceso que produce N datos crecientes positivos y cuando acaba produce un -1
	def producer(self):
		dato = 0
		pid = int(current_process().name)
		for v in range(self.N):
			print (f"producer {pid} produciendo")
			dato += round(random()*10)
			self.addDato(dato, pid) 
			print (f"producer {pid} almacenado {dato}")
		self.addDato(-1, pid) #Para indicar que ha terminado produce un -1, que no se debe almacenar

	#Proceso que consume el menor dato en el storage y lo guarda en el almacén hasta que los productores terminan de producir
	def consumer(self):
		while self.storage[0] != -1 or len(set(self.storage[:])) > 1: #Acaba cuando todos los elementos de storage son -1, es decir, todos los procesos han terminado
			self.storageNoVacio.acquire() #Espera a que el storage no esté vacío
			print ("consumer consumiendo")
			self.merge() #Añade el menor de los datos del storage al almacen

	#Inicia NPROD procesos de producer y un proceso de consumer
	def main(self):
		prodlst = [Process(target=self.producer, name=f'{i}', args=()) for i in range(self.NPROD) ] #Creamos NPROD procesos producer

		conslst = [Process(target=self.consumer, name="cons", args=())] #Creamos un proceso consumer

		for p in prodlst + conslst: #Iniciamos todos los procesos
			p.start()

		for p in prodlst + conslst: #Esperamos a que terminen todos los procesos
			p.join()
			
		print (f"Almacen: {self.almacen[:]}" if len(self.almacen[:]) == self.NPROD*self.N else "Error") #Mostramos el almacén o un mensaje de error si le faltan datos

if __name__ == '__main__':
#Tenemos 3 productores, cada uno crea 1000 datos y tiene una cola de tamaño 10. 1 consumidor.
	N, K, NPROD = 1000, 10, 3
	p1 = practica1(NPROD, N, K) 
	p1.main() #Iniciamos los procesos
