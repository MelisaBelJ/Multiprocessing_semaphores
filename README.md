# Practica1
Los productores van almacenando lo que producen en un buffer de longitud K.
Para cada buffer se necesitan 2 semáforos:
- 1 para comprobar que este no se ha llenado
- 1 para evitar que lo modifiquen el productor y el consumidor simultáneamente.

En paralelo, el consumidor va cogiendo los primeros elementos de cada búffer siempre que los haya.
Para esto, se almacena el primer elemento de cada uno en una lista aparte, que es de la que lee el consumidor. El propósito de esto
es evitar que mientras el consumidor busca el menor elemento de los primeros de cada productor estos no puedan seguir produciendo.

Esta lista tiene 2 Locks, 1 para comprobar que no está siendo usado y otro para comprobar que está lleno antes de que el consumidor intente buscar el mínimo.
