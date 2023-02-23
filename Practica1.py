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
		self.colas      = [Array('i', K) for i in range(NPROD)] #Colas de los productores, para almacenar el resto de productos (a parte del visible para el consumidor)
		self.index      = [Value('i', 0) for i in range(NPROD)] #Posición de la lista que usamos de cola por la que va cada productor
		self.occStorage = Value('i', 0) #Cantidad de posiciones del storage ocupadas

		self.empty	        = [BoundedSemaphore(K) for i in range(NPROD)] #Semaforo para controlar que los productores no hagan más de lo que cabe en la cola
		self.storageLibre   = Lock() #Lock para controlar que el storage no está siendo usado por otros procesos
		self.storageNoVacio = Lock() #Lock para controlar que el consumidor no empiece a consumir hasta que el storage esté ocupado
		self.storageNoVacio.acquire() #El storage empieza vacío por lo que bloqueamos el Lock para que el consumidor espera a que se llene
		
	#Modifica la posicion i de la cola de pid, poniendo dato
	def cambiaCola(self, i, dato, pid):
		self.colas[pid][i] = dato #Añadimos el dato a la cola
		if i == 0: #Si es el primer dato de la cola, lo colocamos en Storage
			with self.storageLibre:
				self.storage[pid] = dato
				self.occStorage.value += 1
				if self.occStorage.value == self.NPROD:
					print("Listos para ser consumidos")
					self.storageNoVacio.release() #Ya se ha llenado el storage, por lo que liberamos el Lock

	#Añade dato a la cola pid
	def addDato(self, dato, pid):
		self.empty[pid].acquire() #Comprobamos que no está llena la cola
		self.cambiaCola(self.index[pid].value, dato, pid)
		self.index[pid].value += 1

	#Devuelve el primer dato de la cola pid
	def getDato(self, pid):
		dato = self.colas[pid][0] 
		self.occStorage.value -= 1
		self.index[pid].value -= 1
		for i in range(self.index[pid].value): #Desplazamos la cola una posición
			self.cambiaCola(i, self.colas[pid][i+1], pid)
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
			dato += round(random()*30)
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

class practica1_VariosConsumidores():
	def __init__(self, N, K, NPROD, NCONS):
		self.K	 = K
		self.N	 = N
		self.NPROD = NPROD
		self.NCONS = NCONS
		
		self.manager = Manager()
		self.almacen = self.manager.list()
		self.storage = Array('i', self.K)
		self.index   = Value('i', 0)
		for i in range(K):
			self.storage[i] = -1

		self.non_empty = Semaphore(0)
		self.empty	   = BoundedSemaphore(self.K)
		self.mutex	   = Lock()
		self.mutex2	   = Lock()

	def addDato(self, dato):
		with self.mutex:
			self.storage[self.index.value] = dato
			self.index.value += 1

	def getDato(self):
		with self.mutex:
			dato, mi = self.storage[0], 0
			for i in range(self.index.value):
				if dato > self.storage[i]:
					mi, dato = i, self.storage[i]
			self.index.value -= 1
			self.storage[mi] = self.storage[self.index.value]
			self.storage[self.index.value] = -1
		return dato
				
	def merge(self, dato):
		with self.mutex2:
			lista = practica1_VariosConsumidores.busqBinaria(self.almacen, dato)
			l = len(self.almacen)
			for i in range(l):
				self.almacen[i] = lista[i]
			self.almacen.append(lista[l])

	def busqBinaria(lista, dato):
		listaReturn, l = [], len(lista)
		if l == 0:
			listaReturn = [dato]
		elif l == 1:
			listaReturn = (
			lista + [dato] if dato > lista[l//2] 
			else [dato] + lista)
		else:
			listaReturn = (
			lista[0:l//2] + practica1_VariosConsumidores.busqBinaria(lista[l//2:l], dato) if dato > lista[l//2] 
			else practica1_VariosConsumidores.busqBinaria(lista[0:l//2], dato) + lista[l//2:l])
		return listaReturn

	def producer(self):
		dato = 0
		for v in range(self.N):
			print (f"producer {current_process().name} produciendo")
			dato += round(random()*30)
			self.empty.acquire()
			self.addDato(dato)
			self.non_empty.release()
			print (f"producer {current_process().name} almacenado {dato}")


	def consumer(self):
		for v in range(self.N):
			self.non_empty.acquire()
			print (f"consumer {current_process().name} desalmacenando")
			dato = self.getDato()
			self.empty.release()
			print (f"consumer {current_process().name} consumiendo {dato}")
			self.merge(dato)

	def main(self):
		prodlst = [ Process(target=self.producer, name=f'prod_{i}', args=())
					for i in range(self.NPROD) ]

		conslst = [ Process(target=self.consumer, name=f"cons_{i}", args=())
					for i in range(self.NCONS) ]

		for p in prodlst + conslst:
			p.start()

		for p in prodlst + conslst:
			p.join()
			
		print (f"Almacen: {self.almacen[:]}" if len(self.almacen[:]) == self.NPROD*self.N else "Error")

if __name__ == '__main__':
#Tenemos 3 productores, cada uno crea 100 datos y tiene una cola de tamaño 10
	N, K, NPROD, NCONS = 100, 10, 3, 1
	if NCONS == 1:
		p1 = practica1(NPROD, N, K) 
	elif NCONS >1:
		p1 = practica1_VariosConsumidores(N, K, NPROD, NCONS)
	else:
		raise TypeError("El número de consumidores no puede ser negativo")
	p1.main() #Iniciamos los procesos
