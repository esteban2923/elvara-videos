# ELVARA – vídeo diario para redes sociales

Este repositorio genera y aloja un vídeo vertical nuevo cada día para la tienda **ÉLVARA** (elvara-beauty.com) y lo publica con Metricool en Instagram, Facebook y TikTok. Trabaja siempre en **español** y para un dueño de tienda sin conocimientos técnicos.

## Datos fijos
- Producto: Élvara – Máscara LED inalámbrica para rostro y cuello, **99 €**, **envío gratis**.
- Metricool: marca "Élvara besito y more", **blogId 7630036**, zona horaria Europe/Madrid. Redes: Instagram @elvarabeautyymore, Facebook "Élvara besito y more", TikTok elvara.beautyymore.
- URL pública de cada vídeo: `https://raw.githubusercontent.com/esteban2923/elvara-videos/main/out/AAAA-MM-DD.mp4`

## Pasos de cada día
1. **Elegir concepto**: `python3 gen.py --list --date HOY` muestra los conceptos válidos hoy (los navideños solo hasta el 25-12). Lee `history.json` y elige uno que **no se haya usado en los últimos 4 días**. Semilla = fecha en número (p. ej. 20261106) para que el vídeo sea distinto aunque se repita concepto.
2. **Previsualizar**: `python3 gen.py --concept X --seed N --date HOY --preview out/prev.jpg` y mira la imagen (Read). Comprueba que los textos se leen y que nada sale cortado. Si algo falla, cambia la semilla.
3. **Renderizar**: `python3 gen.py --concept X --seed N --date HOY --out out/HOY.mp4` (tarda ~1 min). Borra `out/prev.jpg`.
4. **Limpiar**: borra de `out/` los vídeos con más de 10 días para que el repositorio no crezca.
5. **Historial**: añade a `history.json` una entrada `{fecha, concepto, semilla, texto_instagram, audio_instagram, hora}`.
6. **Subir**: `git add -A && git commit -m "Vídeo HOY (concepto)" && git push`. Antes de seguir comprueba que la URL raw responde (el push tarda unos segundos en verse).
7. **Programar en Metricool** (`createScheduledPost`, blogId 7630036) para las **20:30 de hoy** (si ya pasaron, a la próxima hora en punto + 30 min):
   - **Instagram + Facebook** en una sola publicación: `autoPublish: true`, Instagram `type: REEL`, Facebook `type: REEL`, `media: [URL raw]`. Audio de Instagram: elige de `catalog.json → instagram_audio_ids` (lista `christmas` hasta el 25-12, `general` después) uno **distinto del usado ayer** y pásalo como `audioConfiguration.audioId`. Si da error, publica sin audio.
   - **TikTok** en otra publicación: `autoPublish: false` (al usuario le llega un aviso al móvil para poner una canción en tendencia y publicar), `tiktokData: {title: <título corto>, privacyOption: "PUBLIC_TO_EVERYONE", commercialContentOwnBrand: true}`.
8. **Textos**: escribe cada día un texto **nuevo** (no copies los de días anteriores; revisa `history.json`). Gancho en la primera línea, 2-3 frases sobre el producto según el concepto, "99 € · Envío gratis", "👉 elvara-beauty.com (enlace en la bio)", una pregunta para comentarios y 6-9 hashtags (mezcla fijos #ELVARA #mascaraLED con otros del concepto). Para TikTok, texto más corto con #fyp #parati.
   - **Prohibido** prometer resultados médicos o de salud (acné, arrugas, colágeno, curar, eliminar…). Habla de rutina, autocuidado, diseño, modos de luz, comodidad y regalo.
   - Mientras el producto esté "bajo pedido", no prometas entrega antes de Navidad.
9. **Avisar al usuario** con PushNotification: "ELVARA: vídeo de hoy (concepto) programado a las 20:30 en Instagram y Facebook. TikTok: abre el aviso de Metricool a esa hora para ponerle canción." y cualquier problema.

## Si algo falla
- Si `git push` es rechazado o la URL raw no responde, no publiques: avisa al usuario con PushNotification explicando qué pasó.
- Si Metricool pide volver a iniciar sesión, avisa al usuario.
- Nunca publiques dos veces el mismo día: si `history.json` ya tiene la fecha de hoy, no hagas nada y avisa.

## Añadir tomas nuevas
Nuevas tomas van en `assets/clips/cNN.mp4` (1000x720, 30 fps, sin audio) o `assets/photos/pNN.jpg`, y se añaden a la categoría que toque en `catalog.json`.
