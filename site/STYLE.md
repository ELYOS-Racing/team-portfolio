# Guía de estilo del portafolio

Cómo se ve y se mueve el sitio, para que cualquier cambio posterior se vea igual. Qué contenido va y cómo se edita está en [`CONTRIBUTING.md`](../CONTRIBUTING.md); cómo funciona el generador, en [`README.md`](README.md).

## La idea: un cuaderno de ingeniería sobre la mesa de dibujo

El sitio es **una mesa de dibujo (blueprint) con hojas de plano encima**. Todo sale de ese mundo: papel cuadriculado, tinta azul, marcos de plano, cotas, cajetines, globos, notas escritas a mano. Si un elemento nuevo no existiría en un cuaderno de ingeniería o en una lámina de CAD, probablemente no va.

| Capa | Qué es | Dónde |
|---|---|---|
| **Franjas navy** | Cabecera y pie, con el logo oficial en blanco | Todas las páginas |
| **Escenario del hero** | Azul marino profundo con viñeta: el circuito brilla encima | Inicio, Mileage, Autonomous |
| **Mesa blueprint** | Azul medio con rejilla blanca tenue | Fondo de toda la página |
| **Hojas** | Papel crema con tinta: aquí vive el contenido | Secciones, áreas, temporadas, miembros |

## Color

Los valores viven en las variables de `site/style.css`; nunca se escribe un color suelto en un componente.

| Token | Valor | Uso |
|---|---|---|
| Navy de la franja | `#08202F` | Cabecera y pie |
| Mesa `--bg` | `#24476B` | Fondo de la página |
| Texto sobre la mesa `--text` / `--muted` | `#F3F6F9` / `#C9D6E3` | Texto fuera de las hojas (8.6:1 y 6.6:1) |
| Señal `--signal` | `#9CC0FF` | Datos, enlaces y botones sobre la mesa |
| Papel `--paper` | `#F8F4EA` | Hojas |
| Tinta `--ink` | `#17325C` | Texto y líneas sobre el papel (10.6:1) |
| Tinta suave `--ink-soft` / lápiz `--pencil` | `#33496B` / `#575C63` | Texto secundario y etiquetas (7.6:1, 5.9:1) |
| Pluma azul `--pen` | `#1F4FBF` | Énfasis, enlaces y la pieza clave de un diagrama sobre el papel (6.4:1) |
| Resaltador `--hl` | azul al 32 % | Negritas y cifras grandes en las hojas |
| Cuadros | blanco y negro | **Solo** en la línea de salida o meta |

- **El azul es para datos y acciones.** Las etiquetas pequeñas (*eyebrows*) van en plata o tinta, no en azul.
- **Contraste mínimo 4.5:1** para todo texto; si un color nuevo no lo cumple, no se usa.
- El logo **no se recolorea**: va en blanco sobre navy.

## Tipografía

| Familia | Rol | Ejemplo |
|---|---|---|
| **Archivo**, ancho 125, peso 750–850 | Titulares (eco del logotipo extendido) | *One kilowatt-hour, 88 laps.* |
| **Archivo**, ancho 100 | Texto corrido, 17 px, interlineado 1.6 | párrafos, tablas |
| **JetBrains Mono**, mayúsculas, espaciado 0.1–0.14 em | Etiquetas, datos, cajetines, números de plano | `ELY-ENG-03`, `ITEM`, `REV A` |
| **Caveat** | **Solo** notas escritas a mano: márgenes, diagramas, mejoras medidas | *≈ 11 Wh a lap* |

Nunca más de tres familias; nunca Caveat para texto que haya que leer con cuidado.

## Componentes

Todos se generan desde `build.py`; para algo nuevo, se reutilizan estos antes de inventar otro.

| Componente | Función en `build.py` | Reglas |
|---|---|---|
| **Hoja** | `sheet()` | Marco de una línea con zonas A–F / 1–4, número de lámina en contorno, *kicker* en mono, titular, cota que se dibuja con el número `ELY-<código>-<nn>`, nota al margen opcional y **cajetín** al pie, pegado al marco |
| **Nota al margen** | parámetro `note=` | Máximo una por hoja, 2–5 palabras, en inglés, que agregue algo (*"same track = comparable"*), no que repita el título |
| **Tarjetas** | `project_cards()`, `members_list()` | Borde de tinta de 1.5 px; al pasar el cursor se levantan con sombra dura de impresión |
| **Pestañas de separador** | en `project_page()` | Navegación entre áreas en el borde superior de la hoja; la abierta se funde con el papel |
| **Historial** | `history_html()` | Línea de tiempo por temporada con el año grande y la marca *in progress* |
| **Ficha de miembro** | `member_page()` | Monograma a mano, identidad en cuadrícula 2×2, resultados medidos como barras antes/después, revisiones REV A, B…, lista de habilidades |
| **Hero de circuito** | `circuit_hero()`, `track_annotations()` | Circuito brillante con marcas de plano calculadas del trazado y telemetría en vivo |

## Diagramas

Cada área tiene su lámina en `site/diagrams.py`, dibujada como en un curso de CAD o un cuaderno:

- **Lienzo** de 960 × 480 (más alto si hace falta), coordenadas a mano; las primitivas son `box`, `arrow`, `path`, `circle`, `note` y, para láminas de dibujo técnico, `center` (línea de centro), `dim` (cota) y `balloon` (globo con lista de partes).
- **Trazo a mano** como geometría (curvas con semilla), nunca con filtros SVG.
- **Una o dos piezas en pluma azul** (`accent=True`): lo más importante del diagrama. Todo lo demás en tinta.
- **Punteado** para lo oculto, lo que va por debajo o lo que **aún no se elige**; se dice en el subtítulo.
- **Texto** en Caveat: títulos de caja cortos (1–3 palabras) y sus subtítulos; notas de una idea; separar todo texto de líneas y barrenos al menos 12 px.
- **Solo hechos de la página del área**: sin modelos que no sean públicos, sin esquemáticos, sin CAD real.
- Cada lámina lleva **pie** (`CAPTIONS`) de una o dos frases y un **número de figura** en `FIGS` (`build.py`).
- Antes de publicar, revisar la captura a 1280 px: nada se encima, nada se sale de las celdas.

## Movimiento

- Cada movimiento tiene un porqué: la tinta **se dibuja**, las notas aparecen **después** de su línea, el circuito se recorre, las barras **crecen** hasta su valor.
- Solo `transform`, `opacity` y `stroke-dashoffset`; curva `--ease-out` (rápida al entrar, suave al llegar); duraciones de 160–900 ms; ninguna animación de dibujo pasa de unos 3 s en total.
- Todo se detiene fuera de pantalla y con **reduced motion**, que muestra el estado final; el botón *Pause motion* manda en el hero, los diagramas y el coche 3D.

## Accesibilidad

- Contraste ≥ 4.5:1, foco visible (aro de 3 px), objetivos táctiles ≥ 44 px.
- Cada sección con su encabezado; cada dibujo con texto alternativo (`role="img"` y `aria-label`, o descripción en `sr-only`); lo decorativo con `aria-hidden`.
- El orden con teclado sigue el orden visual; nada depende solo del color.
- Probar en 390 px (teléfono), 1280 × 600 y 1536 × 730 (laptop con barras del navegador) y 1920 px.

## Qué no hacer

- Fondos de color nuevos, degradados de moda, sombras suaves de «tarjeta SaaS», emojis como íconos.
- Recolorear el logo o usar el azul en etiquetas decorativas.
- Más de una nota al margen por hoja, o notas que no aportan.
- Diagramas con datos que la página no respalda, o con modelos privados.
- Animaciones que no expliquen nada, o que no respeten reduced motion.
