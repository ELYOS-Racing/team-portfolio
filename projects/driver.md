# Driver del motor

Controlador del motor BLDC del prototipo: convierte el pedal en corriente y la corriente en par, con la menor pérdida posible.

| Aspecto | Detalle |
|---|---|
| Plataforma | Teensy 4.1 (NXP i.MX RT1062, ARM Cortex-M7 a 600 MHz) |
| Software | Teensyduino + FreeRTOS + SimpleFOC, con una capa de abstracción de hardware propia |
| Control | FOC (control vectorial) con sensores Hall; lazo de corriente a 10 kHz |
| Potencia | Inversor trifásico de 48 V |

## Lo que se trabaja para 2027

- Medición de corriente sincronizada con el PWM: el lazo pasó de ≈ 68 µs de cómputo y ≈ 27 µs de jitter a ≈ 5.4 µs y ≈ 0.6 µs (medido en banco, nov-2026).
- Arranque sin sensores de posición y observador sensorless.
- Motor de ≈ 750 W con clutch, operado en su punto de máxima eficiencia.

El código es privado.
