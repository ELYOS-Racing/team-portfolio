# Cómo editar el portafolio

Guía para quien agregue o cambie contenido del portafolio. Si es tu primera vez, empieza por la [guía de entrada](docs/GUIA_DE_ENTRADA.md): cómo se arma el sitio, cómo correrlo y qué archivo editar. El aspecto visual (colores, tipografía, hojas, diagramas) está en [`site/STYLE.md`](site/STYLE.md); los detalles técnicos del generador, en [`site/README.md`](site/README.md).

**Idiomas** (regla 11 de la [gobernanza](https://github.com/ELYOS-Racing/.github/blob/main/GOVERNANCE.md)): el contenido del sitio (`projects/`, `seasons/`, `members/`, `site/data.yaml`) va en **inglés**, porque lo lee gente de fuera. Estas guías, los issues, los PR y los commits van en **español**.

## Qué es este portafolio

El CV del equipo: qué construimos, cómo funciona, qué medimos y quién lo hizo, **sin publicar código ni archivos de diseño**. Cada página explica el trabajo con texto, tablas y un diagrama dibujado a mano; el código y los CAD siguen privados en sus repos.

## Temporadas

Una **temporada** lleva el año de su competencia principal y va de **agosto del año anterior** a esa competencia (o al ADC de junio). La temporada 2027 empezó en agosto de 2026.

El trabajo de cada año queda como evidencia, nunca se borra:

| Dónde | Qué guarda |
|---|---|
| `projects/<área>.md` | **Página viva** del área: arriba el estado actual (resumen, tabla, diagrama); abajo `## History` con una entrada por temporada, la más nueva primero |
| `seasons/<año>.md` | **Bitácora del año**: evento, resultado, plan. El sitio le agrega solo la sección *Work by area* con las entradas de ese año de cada área |
| `site/data.yaml` | Resultados oficiales (tabla del inicio y del README), cifras de la portada y lista de áreas |
| Tag `season-<año>` | **Foto congelada** del repo al cerrar la temporada |

### El historial de un área

Cada entrada es un `### <año> · <titular>` bajo `## History`:

```markdown
## History

### 2028 · Sensorless control on the track (in progress)

- Observer-based start-up running in every attempt; Hall sensors kept as fallback.

### 2027 · Synchronized current sampling and a new motor

- Control-loop compute time from ≈ 68 µs to ≈ 5.4 µs (bench, Nov 2026).
```

- `(in progress)` al final del titular marca la temporada en curso; se quita al cerrarla.
- Titular corto, en inglés, que diga **qué** cambió (no "Updates" ni "Work").
- Viñetas con resultados medibles y su fuente o fecha. Si viene de una temporada, enlaza su página (`[2026 season](../seasons/2026.md)`).
- Las entradas viejas **no se reescriben**: si algo resultó distinto, se corrige en la entrada nueva.
- La última línea de la página (`The code is private.`, `Design files are private.` o `CAD files are private.`) se queda al final, después del historial.

### Al empezar una temporada (agosto)

1. Crear `seasons/<año>.md` con evento, fechas y `Result | Season in progress`.
2. En cada área, agregar arriba del historial la entrada `### <año> · <titular> (in progress)`.
3. Actualizar la parte de arriba de cada área solo cuando algo ya esté en el coche (la tabla describe lo vigente, no lo planeado).

### Al cerrar una temporada (después de la competencia)

1. Agregar el resultado oficial a `site/data.yaml` (`results:`, con su `circuit`) y correr `python site/build.py --write-readme`.
2. Completar `seasons/<año>.md`: resultado, fuentes oficiales.
3. En cada área: quitar `(in progress)`, cerrar las viñetas con lo que realmente se logró y actualizar la tabla de arriba.
4. Revisar las cifras de la portada (`stats:` en `data.yaml`): cada una debe seguir siendo cierta y tener fuente.
5. Mergear y crear el tag: `git tag season-<año> && git push origin season-<año>`.

## Cómo agregar…

| Qué | Pasos |
|---|---|
| **Un miembro** | Lo hace la propia persona: copia `members/TEMPLATE.md` como `members/<usuario-de-github>.md` y abre su PR (ese PR es su consentimiento para publicarlo). La tabla *Measured results* es opcional; cada fila se vuelve una figura |
| **Una temporada de un miembro** | Una sección `## Season <año> · <rol>` nueva arriba de la anterior; se muestra como una revisión más (REV A, B…) |
| **Un área nueva** | `projects/<área>.md` con la misma estructura (primer párrafo = resumen, tabla, `## History`), su entrada en `projects:` de `data.yaml` (con `discipline` y `summary`), y su diagrama (ver [`site/STYLE.md`](site/STYLE.md#diagramas)) |
| **Un resultado** | Fila en `results:` de `data.yaml` con `circuit` (las barras solo comparan dentro del mismo circuito) y `--write-readme` |

## Reglas de redacción

- **Solo hechos con fuente.** Cada cifra sale de un resultado oficial, una medición fechada o un documento del equipo. Lo que es un supuesto o un modelo se dice («in the team's model», «assumed»).
- **Aproximados con ≈**, unidades del SI con espacio (`48 V`, `≈ 5.4 µs`, `336 km/kWh`), miles con coma en inglés (`3,833 m`).
- **Nada privado:** ni código, ni esquemáticos, ni CAD, ni nombres de archivos internos, ni datos personales (teléfonos, correos, direcciones). Los modelos de componentes solo cuando ya son públicos o no revelan estrategia.
- **Frases cortas y activas,** en primera persona del plural («we measured», «our board»), sin adjetivos de marketing.
- **Una idea por viñeta,** empezando por el resultado.

## Flujo de cambios

1. Rama desde `main` (`site/<tema>`, `content/<tema>`).
2. Revisar en local: `pip install markdown pyyaml`, luego `python site/build.py --serve 8000` y abrir <http://localhost:8000/>.
3. `python site/build.py --check-readme` debe pasar (el CI lo revisa).
4. PR en español con qué cambió y por qué; al mergear a `main`, el sitio se publica solo en GitHub Pages.
