# Sistema-port-til-de-monitoreo-cardiaco-con-detecci-n-de-arritmias-para-adultos-mayores

Este proyecto esta diseñado para brindar una opcion economica y viable para el monitorio del ritmo cardiaco (enfocado a adultos mayores)
El dispositivo consta de 2 sensores (Max30102), encargado del monitoreo de la presion sanguinea y (AD8232) encargado de la deteccion de latidos (BPM)
El proposito de nuestro proyecto esta enfocado a la deteccion y prevención de arritmias (Taquicardia y Braquicardia).
Todo esto es procesado en una placa Esp32, y adicionalmente con un filtro en Python para la señal del (AD8232) y detección de picos.
El funcionamiento del proyecto es el siguiente: 
1. Se alimenta el circuito y el sensor (AD8232) con los electrodos conectados al cuerpo del paciente enviaran las señales pre filtradas por el mismo sensor al Esp32.
2. El Esp32 mediante conexión USB se comunica con una PC para aplicar un filtrado en Python que, limpia la señal y detecta los picos (BPM).
3. Python retorna los valores del (BPM) ya calculados al Esp32 que posteriormente los muestra en la apntalla OLED SSD 1306
4. Dependiendo si (BPM)<60 el buzzer sonara indicando braquicardia
5. Caso contrario (BPM)>100 el buzzer sonara indicando una taquicardia
6. El sensor MAX30102 funciona independiente del filtro de Python, su calculo se ahace directamente en el Esp32 y muestra el resultado en la OLED debajo del vlaor de (BPM)
