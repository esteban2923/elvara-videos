# ELVARA – vídeos diarios para redes sociales

Este repositorio genera y aloja cada día **3 reels y 3 historias** verticales nuevos para la tienda **ÉLVARA** (elvara-beauty.com) y los publica con Metricool en Instagram, Facebook y TikTok. Trabaja siempre en **español** y para un dueño de tienda sin conocimientos técnicos.

## Datos fijos
- Producto: Élvara – Máscara LED inalámbrica para rostro y cuello, **99 €**, **envío gratis**.
- Metricool: marca "Élvara besito y more", **blogId 7630036**, zona horaria Europe/Madrid. Redes: Instagram @elvarabeautyymore, Facebook "Élvara besito y more", TikTok elvara.beautyymore.
- URL pública de cada vídeo: `https://raw.githubusercontent.com/esteban2923/elvara-videos/main/out/<archivo>.mp4`

## Plan de cada día (hora de Madrid)
| Franja | Tipo | Archivo | Redes |
|---|---|---|---|
| 11:30 | Historia 1 | `out/HOY-h1.mp4` | Instagram + Facebook (historia) |
| 12:30 | Reel 1 | `out/HOY-1.mp4` | Instagram + Facebook (reel) y TikTok |
| 16:30 | Reel 2 | `out/HOY-2.mp4` | Instagram + Facebook (reel) y TikTok |
| 18:30 | Historia 2 | `out/HOY-h2.mp4` | Instagram + Facebook (historia) |
| 20:30 | Reel 3 | `out/HOY-3.mp4` | Instagram + Facebook (reel) y TikTok |
| 22:30 | Historia 3 | `out/HOY-h3.mp4` | Instagram + Facebook (historia) |

No publiques más que esto: publicar en exceso hunde el alcance y puede hacer que Instagram o TikTok restrinjan la cuenta.

## Pasos de cada día
0. **Comprobar**: si `history.json` ya tiene entradas con la fecha de hoy, no hagas nada y avisa al usuario.
1. **Elegir conceptos**:
   - Reels: `python3 gen.py --list --date HOY`. Elige **3 distintos** que no estén entre los reels de ayer en `history.json`.
   - Historias: `python3 gen.py --list-stories --date HOY` (vídeos de ~7 s). Elige **3 distintos**, evitando si se puede los de ayer.
   - Los conceptos navideños solo salen hasta el 25-12.
   - Semilla = fecha en número + número de franja (reel 1 → 202611111, reel 2 → 202611112, reel 3 → 202611113, historia 1 → 202611114, historia 2 → 202611115, historia 3 → 202611116).
2. **Previsualizar** cada vídeo: `python3 gen.py --concept X --seed N --date HOY --preview out/prev.jpg` y mira la imagen (Read). Comprueba que los textos se leen y que nada sale cortado. Si algo falla, cambia la semilla.
3. **Renderizar** los 6: `python3 gen.py --concept X --seed N --date HOY --out out/<archivo>.mp4` (reel ~1 min, historia ~20 s). Borra `out/prev.jpg`.
4. **Limpiar**: borra de `out/` los vídeos con más de 10 días para que el repositorio no crezca.
5. **Historial**: añade a `history.json` una entrada por publicación: `{fecha, tipo: "reel"|"historia", concepto, semilla, texto_instagram, audio_instagram, hora}` (en historias, `texto_instagram` y `audio_instagram` vacíos).
6. **Subir**: `git add -A && git commit -m "Vídeos HOY" && git push`. Antes de seguir comprueba que las 6 URL raw responden (el push tarda unos segundos en verse).
7. **Programar en Metricool** (`createScheduledPost`, blogId 7630036) cada franja de la tabla. Si una hora ya pasó, sáltala (no la amontones con otra).
   - **Reel, Instagram + Facebook** en una sola publicación: `autoPublish: true`, Instagram `type: REEL` con `showReelOnFeed: true`, Facebook `type: REEL`, `media: [URL raw]`. Audio de Instagram: de `catalog.json → instagram_audio_ids` (lista `christmas` hasta el 25-12, `general` después) usa **uno distinto en cada reel del día**, y si se puede distinto de los de ayer; pásalo como `audioConfiguration.audioId`. Si da error, publica sin audio.
   - **Reel, TikTok** en otra publicación a la misma hora: `autoPublish: false` (al usuario le llega un aviso al móvil para poner una canción en tendencia y publicar). Usa como `media` la URL de Metricool que devolvió la publicación de Instagram/Facebook. `tiktokData: {title: <título corto>, privacyOption: "PUBLIC_TO_EVERYONE", commercialContentOwnBrand: true}`.
   - **Historia**: `providers` instagram + facebook, `autoPublish: true`, `instagramData: {type: "STORY"}`, `facebookData: {type: "STORY"}`, `text: ""` (las historias no llevan texto), `media: [URL raw]`.
8. **Textos de los reels**: escribe cada reel con un texto **nuevo** (no copies los de días anteriores ni los otros reels del día; revisa `history.json`). Gancho en la primera línea, 2-3 frases sobre el producto según el concepto, "99 € · Envío gratis", hasta el 25-12 inclusive la línea "🎁 Código NAVIDAD10: 10 % de descuento hasta el 25 de diciembre" (después del 25-12 quítala; el código caduca), "👉 elvara-beauty.com (enlace en la bio)", una pregunta para comentarios y 6-9 hashtags (mezcla fijos #ELVARA #mascaraLED con otros del concepto). Para TikTok, texto más corto con #fyp #parati.
   - **Prohibido** prometer resultados médicos o de salud (acné, arrugas, colágeno, curar, eliminar…). Habla de rutina, autocuidado, diseño, modos de luz, comodidad y regalo.
   - Mientras el producto esté "bajo pedido", no prometas entrega antes de Navidad.
9. **Avisar al usuario** con PushNotification: "ELVARA: 3 reels (12:30, 16:30, 20:30) y 3 historias programados. TikTok: abre el aviso de Metricool a cada hora de reel para ponerle canción." y cualquier problema.

## Si algo falla
- Si `git push` es rechazado o una URL raw no responde, no publiques ese vídeo: avisa al usuario con PushNotification explicando qué pasó.
- Si Metricool pide volver a iniciar sesión, avisa al usuario.
- Nunca publiques dos veces el mismo día (paso 0).

## Añadir tomas nuevas
Nuevas tomas van en `assets/clips/cNN.mp4` (1000x720, 30 fps, sin audio) o `assets/photos/pNN.jpg`, y se añaden a la categoría que toque en `catalog.json`. Los conceptos con `"story": true` son historias; el resto, reels.
