# Telemetría

Lee los sensores del vehículo, los fusiona, los registra y los transmite a pits en vivo; en cabina, el piloto ve velocidad, mapa y mensajes del equipo.

| Aspecto | 2026 |
|---|---|
| Hardware | ESP32 en PCB propia; display de cabina ESP32-S3 por CAN |
| Sensores | GPS, IMU, tubo Pitot, voltaje, corriente, rpm y acelerador del driver |
| Fusión | Filtro de Kalman extendido con confianza adaptativa según calidad de la señal |
| Enlace | WiFi → backend en la nube → WebSockets → dashboard (entrega de datos de ≈ 535 ms a < 1 ms en benchmark local) |
| Análisis | Canales matemáticos de eficiencia del piloto y del vehículo |

## Lo que se trabaja para 2027

- Medición de energía de precisión en el bus DC, velocidad en las tres ruedas, GNSS con RTK, aire y viento.
- Placa V2 y un **copiloto predictivo**: un modelo entrenado en simulación que recomienda al piloto cuándo acelerar y cuándo planear.

El código es privado.
