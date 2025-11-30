Cambios y mejoras hechos en el proyecto: 

---PRIMER PROTOTIPO---
Elemtos:
- Arduino Nano
- Max30102
- Buzzer electrolitico
- Pantalla Oled SSD 1306
Detalle: (Durante esta fase se calculaban la BPM y la presion sanguinea mediante las señales PPM del sensor MAX30102, pero las medidas no eran muy fiables y demasiado inestables)

---SEGUNDO PROTOTIPO---
Elementos: 
- Arduino Nano
- Max30102
- Buzzer electrolitico
- Pantalla Oled SSD 1306
- Filtro con Python
Detalle: (Durante esta etapa se adiciono un filtro en Python por medio de una conexion USB con una PC para poder filtrar mejor las señales del sensor MAX30102, sin embargo el sensor seguia sin ser muy preciso y empezamos a tener problemas con la capacidad de la memoria flash del Arduino Nano)

---TERCER PROTOTIPO---
Elementos: 
- Esp32
- Max30102
- AD8232
- Buzzer electrolitico
- Pantalla Oled SSD 1306
- Filtro con Python
Detalle: (En esta fase se tuvo a disposicion una memoria amplia, pues se cambio el Arduino Nano por el Esp32, ademas se mejoro el filtro en Pytohn para detectar los picos de las arritmias cardiacas)
