from multiprocessing import Process, Manager, BoundedSemaphore, Semaphore, Lock, current_process, Value, Array
from random import random

class practica1():
	def __init__(self, N, K, NPROD, NCONS):
		self.K	 = K
		self.N	 = N
		self.NPROD = NPROD
		self.NCONS = NCONS
		
		self.manager = Manager()
		self.almacen = manager.list()
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
			lista = practica1.busqBinaria(self.almacen, dato)
			l = len(almacen)
		    for i in range(l):
		        almacen[i] = lista[i]
		    almacen.append(lista[l])

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
			lista[0:l//2] + practica1.busqBinaria(lista[l//2:l], dato) if dato > lista[l//2] 
			else practica1.busqBinaria(lista[0:l//2], dato) + lista[l//2:l])
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
	p1 = practica1(100, 10, 3, 3)
	p1.main()
