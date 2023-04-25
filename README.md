# Practica1
Productores van almacenando lo que producen en un buffet de longitud indefinida.
En paralelo, el/los consumidor va cogiendo del buffer siempre que haya algo.

Hay 2 semáforo para cada buffer, una para indicar que no está lleno, otro que no está vacío.

A parte hay un semáforo para la lista en la que se van poniendo los productos que están al principio de cada buffer, que son los que el consumidor va usando.


También se ha hecho una versión con colas circulares en las que los buffer se gestionan como si fueran circulares.
