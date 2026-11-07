# Cómo escribir guiones que enganchen (v2, 2026-11-07)

Resumen de lo que hacen los Shorts/Reels de gimnasio que mejor funcionan, aplicado a El Chico y El Robot.
Leer ANTES de escribir cada guion. El render (`render_reel.py` v2) ya hace la parte visual sola;
este documento es para el texto.

## Lo que hemos visto en los vídeos que funcionan
- El espectador decide en ~1 segundo si sigue. El "3 segundos" ya es tarde: lo primero que se ve y se oye tiene que ser el gancho.
- Muchos lo ven sin sonido: el texto grande en pantalla tiene que entenderse solo (3-6 palabras).
- En fitness funcionan sobre todo: **corregir un error** ("deja de hacer X así"), **desmontar un mito** (genera comentarios de los dos bandos), **un número que sorprende** y **un reto** ("¿aguantas esto 60 segundos? Casi nadie").
- Los virales cortos duran 15-30 s y tienen un cambio (imagen, sonido o giro) cada 2-3 s.
- Se enseña el resultado o el conflicto primero, nunca la introducción. Nada de "hola", "hoy vamos a ver", contexto o presentaciones.
- Un giro a mitad ("pero lo peor es...") recupera a los que se iban a ir.
- El final que mejor retiene es el que enlaza con el principio (el vídeo "da la vuelta") o una pregunta con dos bandos para comentar.

## Reglas para cada guion
1. **Línea 1 (gancho, 0-2 s)**: el Chico, 4-8 palabras, dichas con total seguridad, en mitad de la acción. Ánimo `orgullo` o `susto` (se mueve más). Tarjeta `titulo` con 2-5 palabras en mayúsculas que se entiendan sin audio, y `sub` con una pregunta o amenaza corta.
2. **Línea 2 (antes de 3 s)**: entra el Robot y **corta** al Chico: `"interrumpe": true`. Frase corta y cínica (máx. 10 palabras), con `sello` si desmonta algo.
3. **Cuerpo (3-20 s)**: 4-6 líneas de máx. 12 palabras cada una. Alternar quién habla. 2-3 tarjetas `dato`/`lista` con un número real y llamativo. El Chico replica con algo absurdo para mantener el humor.
4. **Giro a mitad**: una línea tipo "Pero lo peor no es eso..." / "Y aquí viene lo bueno." con un dato nuevo.
5. **Remate + CTA (últimos 3-4 s)**: chiste final del Robot (pantalla `404` si es humillante) y pregunta con dos bandos ("¿Tú calientas o vas a lo loco?"), tarjeta `cta`. Si se puede, que el remate repita o conteste la frase del gancho (bucle).
6. **Duración**: 7-9 líneas, 20-28 s. El render avisa la duración; si pasa de 32 s, recortar.
7. **Palabras clave** (`clave`): 1-2 por línea, la palabra que más pega (número, insulto cariñoso, la palabra del mito). Salen en caja dorada con zoom de golpe.
8. Ciencia siempre correcta. No inventar estudios ni cifras.

## Fórmulas de gancho (rellenar con el tema del día)
| Tipo | Ejemplo |
|---|---|
| Mito con total seguridad | "La creatina deja calvo. Fijo." |
| Error en directo | "Hoy pecho. Sin calentar. Doscientos kilos." |
| Número absurdo | "Cuarenta y cinco series de pecho. En un día." |
| Resultado primero | "Me he roto la espalda... cogiendo un boli." |
| Reto al espectador | "Si haces esto en el gym, estás perdiendo el tiempo." |
| Confesión | "Llevo un año entrenando y no he crecido nada." |
| Desafío al robot | "Robot, apuesto a que muevo la lavadora yo solo." |

Prohibido en la línea 1: saludos, "hoy", "os voy a contar", preguntas genéricas ("¿sabías que...?") sin conflicto, y frases de más de 8 palabras.

## Caption
Primera línea = el gancho convertido en pregunta polémica (es lo que se ve sin abrir). Luego 2-3 frases de valor, CTA de comentario y los 15 hashtags de siempre.

## Comprobación antes de renderizar
- ¿Se entiende el conflicto con solo ver el fotograma 0 (tarjeta + subtítulo)?
- ¿El Robot habla antes del segundo 3?
- ¿Hay un número o dato que sorprenda?
- ¿Hay giro a mitad?
- ¿El final invita a comentar con dos bandos?

Ejemplo completo con estas reglas: `pipeline/guiones/dia20_eddie_hall_lavadora.json`.
