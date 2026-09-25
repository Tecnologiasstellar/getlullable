"""
Every Spanish word build.py prints, in one place.

The site is published twice: English at the root, Mexican Spanish (es-MX) under
/es/, with the same slugs. The hand-written pages carry their own Spanish
(es/index.html, es/manifesto/, es/press/), the Markdown sources have Spanish
twins (catalog/es/, legal/es/), and this file holds the rest: the words the
templates print, and the Spanish twins of build.py's fact lists.

The copy follows the brand's rules, applied to Spanish:
  - tú, never usted. Gender-neutral about the reader: "hasta que te duermas",
    never "dormido" or "dormida". Mexican usage: "en la noche", "la comida",
    "escoger", "la alarma".
  - Whatever the app itself says stays English: story titles, screen names
    (Tonight, Mornings), genres (Ancient Worlds…), narrator personas, and any
    line quoted from a recording. Everything we say about it is Spanish.
  - The app and its stories are English. Every page that sells the app says
    so, because a buyer who finds out after paying is a refund and a review.
  - The narration is synthesised. Nothing here calls it human.
  - Prices say US$: in Mexico a bare "$" means pesos.
  - Mechanism, never outcome. build.py's claim gate reads Spanish.

UI is keyed by the exact English it replaces. Change an English line in
build.py without changing its key here and the build warns, then shows the
English on the Spanish page until this file catches up.
"""

MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]

# The English "The Blackbird" folds the article into one word; Spanish needs
# the right one per animal.
ARTICLES = {"un": "El", "una": "La"}

AUDIO_NOTE = "Ojo: la app y todas sus historias están en inglés."
AUDIO_CHIP = "En inglés"

UI = {
    # ---- page chrome
    "Stories": "Historias",
    "The Sleep Library": "Biblioteca del sueño",
    "Chronotype quiz": "Test de cronotipo",
    "Get the app": "Descarga la app",
    "Sources": "Fuentes",
    "Keep drifting": "Sigue a la deriva",
    "Last updated": "Actualizado el",

    # ---- essays and the library index
    "essay": "ensayo",
    "story · {mins} min": "historia · {mins} min",
    "The short answer": "La respuesta corta",
    "A question, answered": "Una pregunta, respondida",
    "A definition": "Una definición",
    "A quiet fact-world": "Un mundo de hechos tranquilos",
    "Essay": "Ensayo",
    "min read": "min de lectura",
    "Question": "Pregunta",
    "Definition": "Definición",
    "Fact-world": "Mundo de hechos",
    "Quiet, true things to read at night.": "Cosas tranquilas y verdaderas para leer de noche.",
    "A new one most days. Nothing urgent, ever.": "Uno nuevo de vez en cuando. Nada urgente, nunca.",
    "Quiet, true essays on sleep, racing minds, and pleasantly uneventful knowledge. From "
    "Lullable, the low-arousal knowledge engine.":
        "Ensayos tranquilos y verdaderos sobre el sueño, las mentes aceleradas y el "
        "conocimiento agradablemente sin sobresaltos. De Lullable, el motor de conocimiento "
        "de baja activación.",
    "Lullable reads material like this aloud — warmly, slowly, and quieter every minute —\n"
    "until you drift off somewhere around the fourth clause.":
        "Lullable lee en voz alta material como este —cálido, lento y más bajito cada "
        "minuto— hasta que te duermes por ahí de la cuarta frase.",

    # ---- story pages, hubs, the stories index
    "{title} is {mins} minutes long, read by {narrator}, and ends quieter than it begins. "
    "It lives in the Lullable app.":
        "{title} dura {mins} minutos, la lee {narrator} en inglés y termina más bajito de lo "
        "que empieza. Vive en la app de Lullable.",
    "{mins} minutes · read by {narrator}": "{mins} minutos · leída por {narrator}",
    "Last night, you drifted off during {title}.": "Anoche te dormiste a media historia: {title}.",
    "read by {narrator}": "leída por {narrator}",
    "The kind of sentence people fall asleep during":
        "La clase de frase que nadie alcanza a terminar (en inglés, como en la app)",
    "A Lullable sleep story": "Una historia para dormir de Lullable",
    "{title} — a {mins}-minute sleep story": "{title}: una historia para dormir de {mins} minutos",
    "{n} stories · endings given away": "{n} historias · con el final contado",
    # The English says "every story", and the page lists six. This one does not.
    "Every story in the app.": "Un vistazo a las historias de la app.",
    "Endings given away, nothing withheld.": "Con el final contado, sin guardarnos nada.",
    "Sleep stories": "Historias para dormir",
    "Every sleep story in the Lullable app: slow fiction, nature and weather, folklore — read "
    "warmly and quieter every minute.":
        "Historias para dormir de la app Lullable: mundos antiguos, viajes por el cosmos, "
        "naturaleza tranquila. Leídas en inglés, con calidez y cada vez más bajito.",

    # ---- /creators/ {{launch}}
    "The app is on the App Store. Your link sends iPhones straight to the listing and everyone "
    "else to our site. Apple issues our campaign tag a day or two after launch, and downloads "
    "made before it exists cannot be tied to a code — so wait for our email confirming your "
    "link is tagged before you push. Then go.":
        "La app ya está en el App Store. Tu enlace manda los iPhone directo a la ficha y a todos "
        "los demás a nuestro sitio. Apple nos da la etiqueta de campaña uno o dos días después "
        "del lanzamiento, y las descargas hechas antes de que exista no se pueden ligar a un "
        "código, así que espera nuestro correo confirmando que tu enlace ya está etiquetado "
        "antes de moverlo. Entonces, adelante.",
    "The app is on the App Store. Your link sends iPhones straight to the listing with your tag "
    "attached, and everyone else to our site. Apple counts first-time downloads per tag from the "
    "moment of the tap; there is nothing to wait for.":
        "La app ya está en el App Store. Tu enlace manda los iPhone directo a la ficha con tu "
        "etiqueta incluida, y a todos los demás a nuestro sitio. Apple cuenta las primeras "
        "descargas por etiqueta desde el momento del toque; no hay nada que esperar.",

    # ---- /app/
    "The app": "La app",
    "What Lullable actually does": "Lo que Lullable hace de verdad",
    "Every question about the app, answered in one sentence. Last updated":
        "Cada pregunta sobre la app, respondida en una frase. Actualizado el",
    "Lullable is an iPhone app of {catalogue} long-form sleep stories for adults. One story is "
    "chosen for you on the first screen, so there is nothing to decide at bedtime; a timer set "
    "to 15, 30, 45 or 60 minutes fades to silence rather than stopping; and every recording "
    "fades out on its own in its last thirty seconds. No ads, no streak, no sleep score.":
        "Lullable es una app para iPhone con {catalogue} historias largas para dormir, pensadas "
        "para adultos y narradas en inglés. La primera pantalla ya trae una historia elegida "
        "para ti, así que a la hora de dormir no hay nada que decidir; un temporizador de 15, "
        "30, 45 o 60 minutos se desvanece hasta el silencio en lugar de cortar; y cada "
        "grabación se apaga sola en sus últimos treinta segundos. Sin anuncios, sin rachas, "
        "sin puntaje de sueño.",
    "Lullable is on the App Store. Free to download, and one 40-minute story is free to listen "
    "to end to end before you pay for anything.":
        "Lullable está en el App Store. Descargarla es gratis, y una historia completa se "
        "escucha de principio a fin antes de pagar nada. Las historias están en inglés.",
    'Prefer to read? The Sunday letter is three quiet paragraphs of history or physics, once a '
    'week — <a href="/#signup">join it here</a>.':
        '¿Prefieres leer? La carta de los domingos son tres párrafos tranquilos de historia o '
        'física, una vez por semana y en inglés: <a href="/es/#signup">súmate aquí</a>.',
    "Long-form sleep stories for adults, read slowly and fading to silence.":
        "Historias largas para dormir, para adultos, leídas despacio y que se desvanecen "
        "hasta el silencio.",
    "What Lullable actually does — the app, feature by feature":
        "Lo que Lullable hace de verdad: la app, función por función",
    "Does it fade out? Do I have to choose a story? How long are they? Every question about "
    "the Lullable sleep-story app, answered in one sentence.":
        "¿Se apaga sola? ¿Tengo que escoger una historia? ¿Cuánto duran? Cada pregunta sobre "
        "la app de historias para dormir Lullable, respondida en una frase.",

    # ---- /faq/
    "Questions": "Preguntas",
    "Lullable, answered": "Lullable, pregunta por pregunta",
    "An iPhone app of {catalogue} long-form true stories for adults, read slowly and engineered "
    "to be slept through rather than finished. Free to download, one 40-minute story free in "
    "full, not a medical device.":
        "Una app para iPhone con {catalogue} historias verdaderas y largas para adultos, leídas "
        "despacio y hechas para dormirte a la mitad, no para terminarlas. Gratis para "
        "descargar, con una historia completa gratis. Narrada en inglés. No es un dispositivo "
        "médico.",
    'Open any question for the full answer. Looking for the feature detail — timer lengths, '
    'narrators, lock screen? That is all on <a href="{app}">what the app actually does</a>. '
    'Last updated':
        'Abre cualquier pregunta para ver la respuesta completa. ¿Buscas el detalle de las '
        'funciones: duración del temporizador, narradores, pantalla bloqueada? Todo eso está en '
        '<a href="{app}">lo que la app hace de verdad</a>. Actualizado el',
    "Lullable is on the App Store — free to download, with one 40-minute story free in full, so "
    "you can test it on your own pillow tonight.":
        "Lullable está en el App Store: gratis para descargar, con una historia completa "
        "gratis, para que la pruebes esta misma noche en tu propia almohada. Ojo: las "
        "historias están en inglés.",
    'Not tonight? The Sunday letter is three quiet paragraphs of history or physics, once a '
    'week — <a href="/#signup">join it here</a>.':
        '¿Hoy no? La carta de los domingos son tres párrafos tranquilos de historia o física, '
        'una vez por semana y en inglés: <a href="/es/#signup">súmate aquí</a>.',
    "Long-form true sleep stories for adults, read slowly and fading to silence.":
        "Historias verdaderas y largas para dormir, para adultos, leídas despacio y que se "
        "desvanecen hasta el silencio.",
    "Lullable FAQ — how the sleep-story app works, and what it costs":
        "Preguntas frecuentes de Lullable: cómo funciona la app de historias para dormir y "
        "cuánto cuesta",
    "How does Lullable work? Why does a story quiet a racing mind? What does it cost, and how "
    "is it different from Calm, a podcast or rain sounds? Ten questions, answered.":
        "¿Cómo funciona Lullable? ¿Por qué una historia calma una mente acelerada? ¿Cuánto "
        "cuesta y en qué se distingue de Calm o de un podcast? Once respuestas.",

    # ---- /chronotype/
    "I'm {art} {name}: {line} Find your sleep chronotype in two minutes:":
        "Soy {art} {name}: {line} Descubre tu cronotipo de sueño en dos minutos:",
    "Whatever hour you finally lie down, the moment is the same: a mind still running. Lullable "
    "reads you true, quietly fascinating things in a voice that gets softer every minute, so "
    "the thinking has somewhere to go.":
        "A la hora que por fin te acuestes, el momento es el mismo: una mente que sigue "
        "encendida. Lullable te lee cosas verdaderas y discretamente fascinantes con una voz "
        "que baja cada minuto, para que el pensamiento tenga a dónde ir. Las historias están "
        "en inglés.",
    "Five questions, two minutes": "Cinco preguntas, dos minutos",
    "What's your sleep chronotype?": "¿Cuál es tu cronotipo de sueño?",
    "Lullable has a rule against quizzes. This is the one exception: there are no wrong answers "
    "and nothing to remember.":
        "En Lullable tenemos una regla contra los tests. Esta es la única excepción: no hay "
        "respuestas incorrectas ni nada que recordar.",
    "Most of when you want to sleep was decided for you. A roughly 24-hour clock in your body "
    "cues when you feel sharp, when you feel hungry and when you finally feel tired, and your "
    "<strong>chronotype</strong> is where that clock sits against everyone else's. Early types "
    "peak before lunch. Late types come alive after dark. Most people sit somewhere in the "
    "middle, and the setting drifts with age: children run early, teenagers run late.":
        "Casi todo lo que decide a qué hora te da sueño se decidió sin preguntarte. Un reloj "
        "interno de más o menos 24 horas marca cuándo tienes la cabeza más despejada, cuándo te "
        "da hambre y cuándo por fin te gana el cansancio, y tu <strong>cronotipo</strong> es "
        "dónde queda ese reloj comparado con el de los demás. Los madrugadores rinden más antes "
        "de la comida. Los nocturnos despiertan cuando oscurece. Casi todos quedamos en medio, "
        "y el ajuste se mueve con la edad: los niños tiran a temprano y los adolescentes a "
        "tarde.",
    "The five questions below are adapted from the reduced Morningness–Eveningness "
    "Questionnaire, the short form of the instrument sleep researchers have used since 1976. "
    "Answer for the life you would choose, not the one your alarm imposes.":
        "Las cinco preguntas de abajo son una adaptación del Cuestionario reducido de "
        "Matutinidad-Vespertinidad, la versión corta del instrumento que los investigadores "
        "del sueño usan desde 1976. Contesta según la vida que escogerías, no la que te impone "
        "la alarma.",
    "Reveal my chronotype": "Descubrir mi cronotipo",
    "The five animals": "Los cinco animales",
    "Adapted from Adan &amp; Almirall (1991), the reduced form of Horne &amp; Östberg's "
    "questionnaire. A tendency, not a diagnosis. Chronotypes drift with age and nothing here "
    "is medical advice.":
        "Adaptado de Adan &amp; Almirall (1991), la versión reducida del cuestionario de "
        "Horne &amp; Östberg. Es una tendencia, no un diagnóstico. El cronotipo cambia con la "
        "edad y nada de esto es consejo médico.",
    "What's your sleep chronotype? A two-minute quiz — Lullable":
        "¿Cuál es tu cronotipo de sueño? Un test de dos minutos — Lullable",
    "Five questions from the sleep researchers' own questionnaire, and one of five animals at "
    "the end. Blackbird, tortoise, sheep, moth or octopus?":
        "Cinco preguntas del cuestionario que usan los propios investigadores del sueño, y uno "
        "de cinco animales al final. ¿Mirlo, tortuga, oveja, polilla o pulpo?",
    "Find your sleep chronotype in two minutes · five animals, no wrong answers":
        "Descubre tu cronotipo en dos minutos · cinco animales, ninguna respuesta incorrecta",
    "I'm {art} {name}.": "Soy {art} {name}.",
    "The {name}": "{the} {name}",
    "A sleep chronotype": "Un cronotipo de sueño",
    "{kind} · one of five": "{kind} · uno de cinco",
    "Share my result": "Compartir mi resultado",
    "Copy link": "Copiar enlace",
    'Not you? <a href="{quiz}">Take the two-minute quiz</a>.':
        '¿No eres tú? <a href="{quiz}">Haz el test de dos minutos</a>.',
    "The other four": "Los otros cuatro",
    "Your chronotype": "Tu cronotipo",
    "You’re {art} {name}.": "Eres {art} {name}.",
    "Copied": "Copiado",
    "I'm {art} {name}. What's your sleep chronotype?":
        "Soy {art} {name}. ¿Cuál es tu cronotipo de sueño?",
    "{kind}: {line} Five questions, two minutes, no wrong answers.":
        "{kind}: {line} Cinco preguntas, dos minutos, ninguna respuesta incorrecta.",
}

# The footer every generated Spanish page carries. {year} is filled in by build.py.
FOOTER = """Lullable — el motor de conocimiento de baja activación. La app y sus historias están en inglés. No es un dispositivo médico.
<br>Los ensayos de la Biblioteca del sueño se redactan con Claude siguiendo un contrato de voz fijo, se contrastan con las fuentes que cita cada página y se publican sin edición. La traducción al español de este sitio también se hizo con Claude. ¿Viste un error? <a href="mailto:info@getlullable.com">Avísanos</a> y lo corregimos.
· <a href="/es/">Inicio</a> · <a href="/es/app/">La app</a> · <a href="/es/faq/">Preguntas</a> · <a href="/es/manifesto/">Manifiesto</a> · <a href="/es/sleep/">Biblioteca del sueño</a> · <a href="/es/stories/">Historias</a> · <a href="/es/#signup">Carta de los domingos</a>
<br><a href="https://www.instagram.com/getlullable/" rel="me noopener" target="_blank">Instagram</a> · <a href="https://www.tiktok.com/@getlullable" rel="me noopener" target="_blank">TikTok</a> · <a href="https://www.youtube.com/@lullableapp" rel="me noopener" target="_blank">YouTube</a> · <a href="https://www.facebook.com/profile.php?id=61594011460380" rel="me noopener" target="_blank">Facebook</a>
<br>© {year} Tecnologías Stellar, S.A. de C.V. · desarrollado por <a href="https://stellartech.xyz" rel="noopener" target="_blank">stellartech.xyz</a> · <a href="/es/creators/">Creadores</a> · <a href="/es/support/">Soporte</a> · <a href="/es/privacy/">Privacidad</a> · <a href="/es/terms/">Términos</a> · <a href="#" data-consent>Configuración de cookies</a>"""

# ---------------------------------------------------------------- /chronotype/
# Same questions, same scores, same thresholds and slugs as build.CHRONO_Q and
# build.CHRONO, so a result URL is the same result in both languages. Options
# about how you feel are worded without gender ("con mucho cansancio").
CHRONO_Q = [
    ("Si pudieras organizar tu día con total libertad, ¿a qué hora te levantarías?",
     [("Entre 5:00 y 6:30", 5), ("De 6:30 a 7:45", 4), ("De 7:45 a 9:45", 3),
      ("De 9:45 a 11:00", 2), ("11:00 o más tarde", 1)]),
    ("En la primera media hora después de despertar, ¿cómo te sientes?",
     [("Con mucho cansancio", 1), ("Con algo de cansancio", 2), ("Con bastante energía", 3),
      ("Con mucha energía", 4)]),
    ("En la noche, ¿a qué hora empiezas a sentir cansancio y ganas de dormir?",
     [("De 8:00 a 9:00 p. m.", 5), ("De 9:00 a 10:15 p. m.", 4), ("De 10:15 p. m. a 12:45 a. m.", 3),
      ("De 12:45 a 2:00 a. m.", 2), ("2:00 a. m. o más tarde", 1)]),
    ("¿En qué momento del día estás en tu mejor forma?",
     [("De 5 a 8 a. m.", 5), ("De 8 a 10 a. m.", 4), ("De 10 a. m. a 5 p. m.", 3),
      ("De 5 a 10 p. m.", 2), ("De 10 p. m. a 5 a. m.", 1)]),
    ("Hay gente de mañanas y gente de noches. ¿Tú de cuáles eres?",
     [("Claramente de mañanas", 6), ("Más de mañanas que de noches", 4),
      ("Más de noches que de mañanas", 2), ("Claramente de noches", 0)]),
]
# slug, name, article, lowest score, type line, description, the share line.
CHRONO = [
    ("blackbird", "Mirlo", "un", 22, "Claramente de mañanas",
     "La primera voz del coro del amanecer, cantando antes de que haya luz para cantar. Tu "
     "mejor hora es una que casi todos pasan durmiendo, y a las nueve de la noche el día ya se "
     "cerró en silencio detrás de ti. Rara vez el problema es dormirte. Es que el mundo espera "
     "verte con los ojos abiertos a las diez.",
     "de pie antes que el sol y en la cama antes del noticiero."),
    ("tortoise", "Tortuga", "una", 18, "Más bien de mañanas",
     "Madrugas, vives al ritmo de la luz del día y dentro de ella no tienes prisa. Te despiertas "
     "sin pelearte mucho con la alarma, piensas con más claridad antes de la comida y te vas "
     "apagando al paso de la tarde. Desvelarte se puede, pero se paga a la mañana siguiente.",
     "mi día funciona con luz de sol, y me lo tomo con calma."),
    ("sheep", "Oveja", "una", 12, "Ni una cosa ni otra, y en buena compañía",
     "Ni alondra ni búho, y el más común de los cinco, como era de esperarse. Te despiertas con "
     "la luz, rindes mejor a media jornada y te dan ganas de cama un rato después de que "
     "oscurece. Tu ritmo sigue al sol, con una hora de margen, y por eso una rutina te va tan "
     "bien.",
     "el cronotipo más común, y el único que se cuenta para dormir."),
    ("moth", "Polilla", "una", 8, "Más bien de noches",
     "En la noche es cuando cobras vida, casi siempre cerca de una lámpara. Las mañanas son una "
     "negociación, la tarde va bien, y en algún momento después de la cena empiezan a llegar "
     "las ideas. La medianoche te parece una hora razonable para acostarte, aunque la alarma "
     "opine otra cosa.",
     "mis mejores ideas llegan después de la cena, casi siempre cerca de una lámpara."),
    ("octopus", "Pulpo", "un", 4, "Claramente de noches",
     "No arrancas en serio hasta que se mete el sol. La medianoche es temprano; la una o las dos "
     "es más honesto. Las mañanas, cuando no hay forma de evitarlas, se aguantan. La mente que "
     "te mantiene en vela es la misma que hace su mejor trabajo a las once de la noche, y con "
     "curiosidad para tres corazones necesita un lugar tranquilo a dónde ir cuando termina.",
     "la medianoche es temprano y mi cerebro sale de turno mucho después que yo."),
]

# ---------------------------------------------------------------- /app/
# The Spanish twin of build.APP_FACTS. {catalogue} and {store} are filled in by
# build.py. Two additions carry the one fact a Spanish reader needs and the
# English page never had to say: the stories are narrated in English. The
# question "is it in Spanish?" itself lives on /faq/ only — overlapping
# FAQPage blocks on one domain compete with each other.
APP_FACTS = [
    ("¿Qué es Lullable?",
     "Lullable es una app para iPhone de historias largas para dormir, pensada para adultos: "
     "{catalogue} historias verdaderas y discretamente fascinantes —unas termas romanas a la "
     "hora del cierre, la vida de una secuoya, los anillos de Saturno— leídas despacio y sin "
     "énfasis por un narrador con nombre, y hechas para que te duermas a medio camino. Está "
     '<a href="{store}">en el App Store</a>, gratis para descargar. Las historias están '
     "narradas en inglés."),

    ("¿Las historias se apagan solas?",
     "Sí. Un temporizador de 15, 30, 45 o 60 minutos termina con una bajada de diez segundos "
     "hasta el silencio, no con un corte seco. Además, cada grabación termina así por su "
     "cuenta: los últimos treinta segundos de todas las historias se desvanecen. No hay nada "
     "que apagar."),

    ("¿Tengo que escoger una historia?",
     "No. La primera pantalla es Tonight, y trae una sola historia ya elegida para ti, con un "
     "solo botón de Play. Sin feed, sin una biblioteca que recorrer con el teléfono a quince "
     "centímetros de la cara. La biblioteca completa está ahí si la quieres, pero es la "
     "segunda pantalla, no la primera."),

    ("¿Cuánto duran las historias?",
     "Entre 20 y 41 minutos. La mayoría ronda los 40: lo bastante largas como para que nadie "
     "espere que llegues al final, que es justo la idea."),

    ("¿De qué tratan las historias?",
     "Cuatro categorías, con los nombres que tienen en la app: Ancient Worlds (mundos "
     "antiguos), Cosmic Journeys (viajes cósmicos), Gentle Nature (naturaleza tranquila) y "
     "Cozy Tales (relatos acogedores). Todo es material verdadero, no ficción, contado en orden "
     "y con el final revelado en la primera línea, para que nunca haya motivo para seguir en "
     "vela esperándolo."),

    ("¿Tiene anuncios?",
     "No. Lullable no tiene publicidad, y ninguna versión de este negocio la tiene: un anuncio "
     "a media historia a las 3 de la mañana despierta justo a la persona a la que se lo "
     "vendieron."),

    ("¿Sigue sonando con la pantalla bloqueada?",
     "Sí. Reproducción en segundo plano y con la pantalla bloqueada, con los controles en la "
     "pantalla de bloqueo. Pon el teléfono bocabajo y olvídate de él."),

    ("¿Desde dónde retoma a la noche siguiente?",
     "Desde un minuto antes de donde perdiste el hilo; no desde el punto donde se detuvo el "
     "audio, que siempre es más tarde que el momento en que dejaste de escucharlo."),

    ("¿Hay rachas, puntajes o gráficas de sueño?",
     "Ninguna de las tres. La pantalla de la mañana muestra la última línea que escuchaste y "
     "la hora en que dejaste de escuchar. Es todo lo que sabe y todo lo que afirma. No hay un "
     "número que subir ni nada que mantener."),

    ("¿Quién lee las historias?",
     "Narradores con nombre, en voces masculinas y femeninas: David from Oxford, Amy from "
     "Greenwich, Arthur from Ludlow, Brian from St Ives, Niamh from Kinsale y Patrick from "
     "Block Island. Todos leen en inglés, en tono plano y cálido, quitando énfasis en lugar de "
     "agregarlo, y cada vez más bajito a lo largo del episodio."),

    ("¿Cuánto cuesta?",
     "Descargarla es gratis, y una historia —Aristotle, the Greatest Philosopher, de 33 "
     "minutos— se escucha gratis completa. El resto del catálogo necesita Lullable Premium, "
     "que hoy cuesta US$2.99 al mes o US$19.99 al año en el App Store de Estados Unidos. Apple "
     "fija el precio en cada país y puede cambiar; en México lo verás en pesos en la ficha del "
     "App Store, y esa es la cifra que cuenta."),

    ("¿Hay versión para Android?",
     "Todavía no. Solo iPhone."),

    ("¿Lullable es un dispositivo médico o un tratamiento para el insomnio?",
     "No, y no pretende serlo. Es audio pensado para personas cuya mente no se apaga de "
     "noche. Si tienes insomnio clínico, consulta a un médico."),
]

# ---------------------------------------------------------------- /faq/
# The Spanish twin of build.FAQ_FACTS, plus one question the English page never
# needed: whether it is in Spanish. It sits second, where a Spanish reader looks.
FAQ_FACTS = [
    ("¿Cómo funciona Lullable?",
     "Le das play una vez. Un narrador con nombre te lee una historia verdadera —la vida de "
     "una secuoya, unas termas romanas a la hora del cierre, los anillos de Saturno— despacio, "
     "en tono plano y un poco más bajito cada minuto. En algún punto de la mitad dejas de "
     "seguirla. La historia continúa sin ti y se desvanece sola hasta el silencio. En la "
     "mañana, la app te muestra la última línea que escuchaste y la hora en que dejaste de "
     "escuchar, y a la noche siguiente vuelve a empezar un minuto antes. No hay nada que "
     "configurar, nada que puntuar y nada que terminar."),

    ("¿Está en español?",
     "Este sitio sí; la app y sus historias, no. Todo el audio está en inglés, leído despacio "
     "y con voz plana, y por ahora la app no tiene versión en español. Si dudas de tu inglés "
     'a medianoche, escucha la <a href="/es/#listen">muestra de cuatro minutos</a> antes de '
     "descargarla: es exactamente lo que vas a oír."),

    ("¿Por qué una historia calma una mente acelerada, y el silencio de la cama no?",
     "Porque una mente que no se detiene es más fácil de ocupar que de vaciar. Estar a oscuras "
     "no le da a tu atención nada de qué agarrarse, así que regresa al correo, a la hipoteca, "
     "a lo que dijiste en 2011. Una historia verdadera contada en orden, en tono plano, sin "
     "suspenso y con el final revelado en la primera línea, le da a la atención un lugar "
     "aburrido donde descansar. Ese es todo el diseño de la app. Es un mecanismo, no una "
     "promesa: el sueño no es algo que un software te pueda entregar."),

    ("¿Cuánto cuesta Lullable?",
     "Descargar la app es gratis, y una historia completa —Aristotle, the Greatest "
     "Philosopher, de 33 minutos— se escucha gratis de principio a fin, para que pruebes la "
     "voz en tu propia almohada antes de pagar nada. El resto del catálogo necesita Lullable "
     "Premium: US$2.99 al mes o US$19.99 al año en el App Store de Estados Unidos hoy. Apple "
     "fija el precio en cada país y puede cambiar; en México lo verás en pesos en la ficha del "
     "App Store, y esa es la cifra que cuenta. Como referencia de lo que cobra la categoría: "
     "Calm cuesta US$14.99 al mes y Headspace US$12.99 al mes en el App Store de Estados "
     "Unidos, ambos consultados en la fuente el 7 de septiembre de 2026."),

    ("¿Vale la pena pagar por una app de historias para dormir?",
     "Pruébala antes de decidir; por eso la historia gratis no es un tráiler: misma duración, "
     "mismo narrador, mismo desvanecimiento que las de pago. Una semana con ella te dice más "
     "que cualquier reseña. Lo que agrega la suscripción es el resto del catálogo "
     "—{catalogue} historias, una nueva casi cada semana— y una app sin publicidad, algo que "
     "importa más a la 1 de la mañana que a cualquier otra hora, porque un anuncio a media "
     "historia despierta justo a la persona a la que se lo vendieron. Pon la cifra mensual "
     "junto a los cuarenta minutos por noche que ya pasas en el teléfono, y decide a partir de "
     "ahí."),

    ("¿En qué se diferencia Lullable de Calm o Headspace?",
     "Calm y Headspace son apps de bienestar amplias —meditación, ejercicios de respiración, "
     "música, cursos, lecturas de celebridades— con una sección de sueño entre todo eso. "
     "Lullable hace una sola cosa: historias verdaderas y largas para adultos, leídas para que "
     "te duermas escuchándolas. Sin meditación, sin ejercicios de respiración, sin rachas, "
     "sin puntaje de sueño, sin un feed que recorrer antes de dormir. Su contenido para dormir "
     "es sobre todo ficción y relajación guiada; el nuestro es material real, contado en "
     "orden. Cuestan US$14.99 y US$12.99 al mes, respectivamente, en el App Store de Estados "
     "Unidos (consultado el 7 de septiembre de 2026); Lullable se descarga gratis y trae una "
     "historia completa gratis."),

    ("¿Por qué no poner simplemente un podcast o un audiolibro?",
     "Porque los dos están hechos para que sigas escuchando, y a medianoche ese es el objetivo "
     "equivocado. Un podcast tiene a dos personas interrumpiéndose, risas, un salto de volumen "
     "para leer un anuncio y un conductor cuyo trabajo es que regreses la próxima semana. Un "
     "audiolibro tiene una trama que te castiga por distraerte. Lullable está hecho al revés: "
     "una sola voz, sin segundo interlocutor, sin suspenso, con el volumen bajando a lo largo "
     "del episodio y unos últimos treinta segundos que se desvanecen hasta el silencio. Todo lo "
     "que está hecho para retener la atención es la herramienta equivocada para soltarla."),

    ("¿Una historia para dormir es mejor que el ruido blanco o los sonidos de lluvia?",
     "Es otro trabajo, y cuál te conviene depende de qué te está quitando el sueño. El ruido "
     "tapa el cuarto —el tráfico, tu pareja, una pared delgada—, pero no le da nada que hacer a "
     "una mente ocupada, y por eso hay quien se queda escuchando la lluvia y pensando de todos "
     "modos. Una historia ocupa la parte de la mente que narra. Si el problema es la calle, "
     "usa ruido blanco. Si el problema es tu propio comentario interno, una historia es mejor "
     "herramienta, y nada te impide usar las dos."),

    ("¿Me va a funcionar si la meditación nunca me ha funcionado?",
     "Es exactamente para quien está hecha. La meditación te pide vaciar la mente y notar, sin "
     "juzgarte, cada vez que se distrae, lo cual, para una mente que ya va acelerada, es una "
     "tarea más en la que fallar a medianoche. Lullable no te pide nada. Le das play y alguien "
     "te explica cómo se construyó una catedral. No hay práctica en la que fallar, ni "
     "respiraciones que contar, ni distracciones que atrapar."),

    ("¿De verdad aprendo algo si me duermo a la mitad?",
     "Te quedas con lo que alcanzaste a oír antes de dormirte, que suele ser los primeros diez "
     "minutos, y la pantalla de la mañana te muestra la última línea que escuchaste, así que "
     "esa parte no se pierde. Ese es el punto de la categoría: todo en Lullable es verdadero "
     "—la nieve marina, el ancho estándar de las vías del tren, el clima en el fondo del mar—, "
     "así que el tramo que alcanzas a escuchar vale la pena, y el que te duermes no es una "
     "trama que luego tengas que ir a buscar."),

    ("¿Para quién es Lullable, y para quién no?",
     "Para adultos que no pueden desconectarse de noche: mentes que no se apagan, quienes se "
     "despiertan a las 3 de la mañana, quienes probaron una app de meditación y rebotaron, "
     "quienes antes se dormían con documentales. Está escrito para una atención adulta: sin "
     "cuentos de hadas, sin vocecitas de bebé. No es una app para niños, no es un dispositivo "
     "médico y no es un tratamiento para el insomnio, ni dice serlo. Si tienes insomnio "
     "clínico, consulta a un médico."),
]

# ---------------------------------------------------------------- story hubs
# slug -> (nav, title, h1, description, intro). Same facets and the same
# stories as build.py's `hubs`; only the words change. Two corrections against
# the English on purpose: the story pages carry each story's first minute, not
# its full text, and every recording is in English. The English hubs still say
# "written out in full" — that is a bug in the English copy, reported, and not
# one to translate.
HUBS = {
    "boring-true-stories-to-read": (
        "Para leer",
        "Historias verdaderas para leer antes de dormir",
        "Historias verdaderas (y un poco aburridas) para leer antes de dormir.",
        "Cada historia de la app, presentada en español y con su primer minuto por escrito, en "
        "inglés como suena en la app. El final, contado desde la primera línea.",
        "Cada historia de la app se escribe antes de leerse en voz alta, y en estas páginas "
        "está el principio de cada una: una presentación en español y el primer minuto tal como "
        "suena en la app, en inglés. No es el texto completo; es suficiente para saber de qué "
        "va y para decidir si esa voz es la tuya.\n\n"
        "No son ficción. Unas termas romanas a la hora en que se apagan los fuegos, el museo de "
        "las cosas que se han ido al fondo del mar, la discusión de once años sobre el ancho de "
        "una tarima de madera. El material es verdadero, y está escogido por ser genuinamente "
        "interesante y totalmente intrascendente: aquí nada se resuelve, nada está en juego y "
        "nadie espera a que descubras qué pasa.\n\n"
        "Cada una cuenta su final en el primer minuto. Ese es todo el mecanismo: una historia "
        "cuyo final ya conoces es una historia que tienes permiso de dejar. Leer en la cama "
        "suele fallar porque el libro quiere retenerte. Estas quieren perderte.\n\n"
        "Si prefieres que te las lean, las mismas historias están narradas en la app, en "
        "inglés: [con voz masculina](/es/stories/male-voice/) o femenina."),
    "male-voice": (
        "Voz masculina",
        "Historias para dormir con voz masculina",
        "Historias para dormir con voz masculina.",
        "Las historias de Lullable que narran David, Arthur, Brian y Patrick, en inglés: "
        "graves, sin prisa y más bajitas cada minuto. El primer minuto de cada una, por escrito.",
        "Qué voz te duerme no es una preferencia de la que alguien te pueda convencer, y es de "
        "las pocas cosas del audio para dormir que vale la pena escoger a propósito. Hay quien "
        "necesita un registro más grave para dejar de seguir las palabras; a otros eso mismo "
        "les suena demasiado a alguien leyéndoles las noticias.\n\n"
        "Estas son las historias que leen David from Oxford, Arthur from Ludlow, Brian from St "
        "Ives y Patrick from Block Island, todas en inglés. Lo que tienen en común no es el "
        "tono sino el ritmo: nada de actuación, nada de personajes, nada de cargar una palabra "
        "para avisarte que importa. La lectura aplana en lugar de dramatizar, y el último "
        "tercio de cada grabación es más bajo y más lento que el primero, a propósito, lo "
        "alcances a notar o no.\n\n"
        "Si ninguna te funciona, el primer minuto de cada una está [por escrito para "
        "leerlo](/es/stories/boring-true-stories-to-read/) si prefieres no escuchar. Ninguna "
        "tiene anuncios ni música."),
    "female-voice": (
        "Voz femenina",
        "Historias para dormir con voz femenina",
        "Historias para dormir con voz femenina.",
        "Las historias de Lullable que narran Amy y Niamh, en inglés: cálidas, planas y más "
        "bajitas cada minuto. El primer minuto de cada una, por escrito.",
        "Qué voz te duerme no es una preferencia de la que alguien te pueda convencer, y es de "
        "las pocas cosas del audio para dormir que vale la pena escoger a propósito. Hay quien "
        "se acomoda mejor con un registro más agudo; a otros les lleva demasiada claridad a un "
        "cuarto oscuro.\n\n"
        "Estas son las historias que leen Amy from Greenwich y Niamh from Kinsale, en inglés. "
        "Lo que tienen en común no es el tono sino el ritmo: nada de actuación, nada de "
        "personajes, nada de cargar una palabra para avisarte que importa. La lectura aplana en "
        "lugar de dramatizar, y el último tercio de cada grabación es más bajo y más lento que "
        "el primero, a propósito, lo alcances a notar o no.\n\n"
        "Si ninguna te funciona, el mismo catálogo [con voz masculina](/es/stories/male-voice/) "
        "está a una página, y el primer minuto de cada una está [por escrito para "
        "leerlo](/es/stories/boring-true-stories-to-read/) si prefieres no escuchar. Ninguna "
        "tiene anuncios ni música."),
}
