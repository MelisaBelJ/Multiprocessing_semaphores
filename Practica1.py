from multiprocessing import Process, Manager, BoundedSemaphore, Semaphore, Lock, current_process, Value, Array
from time import sleep
from random import random


N = 100
K = 10
NPROD = 3
NCONS = 3

def add_data(storage, index, pid, data, mutex):
    mutex.acquire()
    try:
        storage[index.value] = data
        index.value = index.value + 1
    finally:
        mutex.release()

def get_data(storage, index, mutex):
    mutex.acquire()
    try:
        dato, mi = storage[0], 0
        for i in range(index.value):
            if dato > storage[i]:
                mi, dato = i, storage[i]
        index.value = index.value - 1
        storage[mi] = storage[index.value]
        storage[index.value] = -1
    finally:
        mutex.release()
    return dato


def producer(storage, index, empty, non_empty, mutex):
    dato = 0
    for v in range(N):
        print (f"producer {current_process().name} produciendo")
        dato += round(random()*30)
        empty.acquire()
        add_data(storage, index, int(current_process().name.split('_')[1]),
                 dato, mutex)
        non_empty.release()
        print (f"producer {current_process().name} almacenado {dato}")


def consumer(storage, almacen, index, empty, non_empty, mutex, mutex2):
    for v in range(N):
        non_empty.acquire()
        print (f"consumer {current_process().name} desalmacenando")
        dato = get_data(storage, index, mutex)
        empty.release()
        print (f"consumer {current_process().name} consumiendo {dato}")
        merge(almacen, dato, mutex2)
            
def merge(almacen, dato, mutex2):
    mutex2.acquire()
    try:
        lista = busqBinaria(almacen, dato)
        l = len(almacen)
        for i in range(l):
            almacen[i] = lista[i]
        almacen.append(lista[l])
    finally:
        mutex2.release()

def busqBinaria(lista, dato):
    l = len(lista)
    if l == 0:
        return [dato]
    elif l == 1:
        if dato > lista[l//2]:
            return lista + [dato]
        else:
            return [dato] + lista
    else:
        if dato > lista[l//2]:
            return lista[0:l//2] + busqBinaria(lista[l//2:l], dato)
        else:
            return busqBinaria(lista[0:l//2], dato) + lista[l//2:l] 

def main():
    manager = Manager()
    almacen = manager.list()
    storage = Array('i', K)
    index   = Value('i', 0)
    for i in range(K):
        storage[i] = -1

    non_empty = Semaphore(0)
    empty     = BoundedSemaphore(K)
    mutex     = Lock()
    mutex2    = Lock()

    prodlst = [ Process(target=producer, name=f'prod_{i}', args=(storage, index, empty, non_empty, mutex))
                for i in range(NPROD) ]

    conslst = [ Process(target=consumer, name=f"cons_{i}", args=(storage, almacen, index, empty, non_empty, mutex, mutex2))
                for i in range(NCONS) ]

    for p in prodlst + conslst:
        p.start()

    for p in prodlst + conslst:
        p.join()
        
    print ("almacen final", almacen[:])


if __name__ == '__main__':
    main()
