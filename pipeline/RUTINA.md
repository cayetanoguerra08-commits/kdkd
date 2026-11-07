# Pasos técnicos para crear y publicar un Reel (El Chico y El Robot)

Referencia técnica del flujo. Qué publicar y cuándo lo decide el usuario en su tarea programada.

## 1. Preparar (≈20 s)
```
bash pipeline/setup.sh
export KOKORO_DIR=/mnt/project-files/pipeline-cache/kokoro   # o la ruta que imprima setup.sh
```

## 2. Elegir tema
- Lista: `pipeline/temas.md` (100 temas). Usados: `pipeline/publicados.md`.
- El día con número más bajo que no esté en `publicados.md`.

## 3. Guion JSON
**Leer antes `pipeline/GANCHOS.md`** (reglas de gancho y ritmo, obligatorias). Si ya existe `pipeline/guiones/diaNN_*.json` para el día elegido, usarlo tal cual.
Misma estructura que `pipeline/guiones/dia20_eddie_hall_lavadora.json` (ejemplo v2), en `pipeline/guiones/diaNN_<slug>.json`.
- 7-9 líneas, 20-28 s. Español de España, frases cortas (máx. 12 palabras; el gancho, máx. 8).
- Línea 1: gancho del Chico (mito absurdo o error exagerado) con tarjeta `titulo` de 2-5 palabras: se ve desde el fotograma 0.
- Línea 2: el Robot le corta antes del segundo 3 con `"interrumpe": true`.
- Un giro a mitad ("Pero lo peor no es eso...") y final con pregunta de dos bandos.
- El Robot: sarcástico, con ciencia real y datos correctos. No inventar estudios.
- 2-3 tarjetas `dato`/`lista`; un `sello` (MITO, ERROR...) al desmontar el mito.
- Remate cómico + última línea CTA con tarjeta `cta`.
- En `voz`, números con letras. Sin emojis.
- `animo` del chico: normal | orgullo | susto | sufre. `pantalla` del robot: ojos | rayas | 404.

## 4. Render (≈40 s)
`python3 pipeline/render_reel.py pipeline/guiones/diaNN_slug.json /tmp/diaNN_slug.mp4` → `"ok": true`.

## 5. URL pública
`bash pipeline/subir_video.sh /tmp/diaNN_slug.mp4 diaNN_slug` → URL raw (rama `video`, se reemplaza en cada subida; el repo no crece).

## 6. Instagram (vidIQ)
1. `vidiq_video_upload` con la URL raw → `videoUrl`.
2. `vidiq_instagram_publish_reel`: `platformAccountId` 28882653428064891, `videoUrl`, `caption`, `isAiGenerated: true`.
3. Repetir con `containerId` cada ~10 s hasta `PUBLISHED`.
4. Si responde "inconclusive", seguir consultando el mismo containerId (suele acabar en PUBLISHED). No crear otro.
5. Si el acceso de Instagram caducó: parar y avisar (hay que reconectar Instagram en vidIQ).

Caption: primera línea = el gancho como pregunta polémica + 2-3 frases con el dato clave + CTA de comentario + 15 hashtags:
`#gym #gimnasio #fitness #gymhumor #humorgym #musculacion #entrenamiento #gymespaña #fitnessespañol #gymtips #consejosgym` + 4 del tema.

## 7. YouTube Shorts (Metricool, blogId 7943370), sin TikTok
Solo en la ejecución de las 17:50 y en días impares (límite gratis: 20 publicaciones/mes). Si `getBrandSettings` no muestra youtubeData, saltar. `createScheduledPost`, fecha = ahora + 5 min (Atlantic/Canary):
```
{"autoPublish": true, "draft": false, "text": "<descripción>", "media": ["<URL raw>"],
 "providers": [{"network": "youtube"}],
 "youtubeData": {"title": "<≤ 70 caracteres> #shorts", "type": "short", "privacy": "public",
   "tags": ["gym","gimnasio","fitness","humor gym", "..."], "category": "COMEDY", "madeForKids": false}}
```
Descripción: 2 frases + CTA + `#shorts #gym #gimnasio #fitness #gymhumor` + 2 del tema.
Metricool copia el vídeo a su servidor al crear la publicación, así que reemplazar la rama `video` después no afecta.

## 8. Registro
Añadir línea a `pipeline/publicados.md`, commit del guion y registro, `git push origin HEAD:main`.
