"""Reseñas de MUESTRA para desarrollo. No son de compradores reales y se marcan `is_demo=True`.

Sustituyen a las 6 reseñas idénticas que el sitio original repetía en las 30 páginas de detalle.
Se pueden borrar todas filtrando por `is_demo` sin tocar reseñas reales.

Clave: la clave del libro en el sitio original (`saleXxx`) o `list:<título>` si solo estaba en un listado.
Valor: [(autor, estrellas, comentario), …]. "Mi Lucha (Lite)" no lleva reseñas de muestra a propósito.
"""

DEMO_REVIEWS: dict[str, list[tuple[str, int, str]]] = {
    "sale1984": [
        ("Sebastián G.", 5, "Una distopía que sigue vigente: la vigilancia constante y la Neolengua dan escalofríos. La edición en inglés de Penguin es cómoda de leer."),
        ("Laura P.", 4, "Pensé que sería una lectura densa y me enganchó enseguida. El final me dejó sin aliento, aunque el ritmo baja un poco a mitad del libro."),
    ],
    "saleAlasSangre": [
        ("Daniela M.", 5, "Violet y el Colegio de Guerra de Basgiath me tuvieron leyendo hasta la madrugada. Los dragones y la tensión romántica están muy bien llevados, y la tapa dura es preciosa."),
        ("Julián T.", 4, "Muy entretenida y adictiva, aunque el sistema de magia se explica poco. Ideal si disfrutas la fantasía romántica."),
    ],
    "saleAnnaK": [
        ("Marta L.", 5, "Una obra maestra sobre el amor, la sociedad rusa y las consecuencias de las decisiones. Son más de mil páginas y valen cada una."),
        ("Ricardo A.", 4, "La historia de Levin y Kitty me gustó tanto como la de Anna. Es un libro pesado para cargar, pero la lectura lo compensa."),
    ],
    "saleAppleMan": [
        ("Felipe C.", 5, "Isaacson retrata a Jobs sin idealizarlo: su genio, su obsesión por el diseño y también su carácter difícil. Se lee como una novela."),
        ("Natalia V.", 4, "Muy completa y bien documentada. Algunas partes sobre negociaciones empresariales se hacen largas, pero vale la pena."),
    ],
    "saleBrujaVerde": [
        ("Paola S.", 3, "Tiene buenas ideas para armar un jardín con intención, pero esperaba más guías prácticas de cultivo."),
        ("Camilo R.", 2, "Interesante como introducción, aunque me pareció superficial en la parte de jardinería. Está más enfocado en la tradición esotérica que en cultivar."),
    ],
    "saleBrumaTrio": [
        ("Andrea F.", 5, "El sistema de magia de la alomancia es de lo mejor que he leído, y el giro final del primer libro es memorable. Tres libros en un solo estuche."),
        ("Mateo Q.", 5, "Vin y Kelsier son personajes inolvidables. La trilogía cierra de forma muy satisfactoria."),
    ],
    "saleCCM": [
        ("Vanessa H.", 4, "Fábula corta y amena sobre liderazgo: usar cabeza, corazón y manos para transformarse. Se lee en una tarde."),
        ("Héctor D.", 4, "La trama es sencilla, pero deja ideas prácticas para el trabajo en equipo. Buen regalo para alguien que empieza a liderar."),
    ],
    "saleCienAnios": [
        ("Isabel N.", 5, "Macondo se queda contigo. La saga de los Buendía mezcla lo cotidiano y lo mágico con una naturalidad única. Un libro para releer."),
        ("Tomás B.", 5, "Al principio me perdí entre tantos Aurelianos y José Arcadios; hacer un pequeño árbol genealógico ayuda. Termina siendo una experiencia inolvidable."),
    ],
    "saleCorteNieblaFuria": [
        ("Carolina Z.", 5, "La evolución de Feyre y la Corte de la Noche es lo mejor de la saga. Ritmo, romance y una trama que va subiendo de intensidad."),
        ("Esteban O.", 4, "Mejora mucho respecto al primer libro. La edición especial es bonita; el romance domina, pero la política entre cortes también engancha."),
    ],
    "saleCrimeCastigo": [
        ("Gabriela T.", 5, "La angustia y la culpa de Raskólnikov están retratadas de forma magistral. Una novela psicológica que no ha envejecido."),
        ("Nicolás E.", 4, "Es intensa y algo densa en los diálogos filosóficos, pero el duelo con el investigador Porfirio es genial."),
    ],
    "saleDickBlackCooks": [
        ("Rodrigo J.", 4, "El capitán Ahab es un personaje formidable. Los capítulos sobre cetología son largos, pero dan textura a la aventura."),
        ("Adriana K.", 5, "Mucho más que la historia de una ballena: es una reflexión sobre la obsesión. La edición es muy legible."),
    ],
    "saleDino": [
        ("Óscar M.", 5, "Impresionante material ilustrativo y muy riguroso sobre terópodos. Para apasionados de la paleontología es una joya."),
        ("Lucía G.", 4, "Muy completo, con diagramas y reconstrucciones a todo color. Es un libro grande y técnico, más de consulta que de lectura seguida."),
    ],
    "saleElCachonDeWill": [
        ("Diego P.", 5, "Will Smith cuenta su infancia, su ascenso a la fama y sus inseguridades con mucha honestidad. Se lee muy rápido."),
        ("Sofía A.", 4, "Ameno y sincero, con una escritura ágil. Algunas partes sobre superación se repiten un poco, pero conmueve."),
    ],
    "saleEnAgosto": [
        ("Beatriz L.", 4, "Una novela breve y sensible sobre Ana Magdalena Bach y sus viajes anuales a la isla. Se siente como un regalo póstumo."),
        ("Alejandro V.", 4, "Corta y de lectura ligera; no es su obra más ambiciosa, pero conserva su prosa inconfundible."),
    ],
    "saleGuerraPaz": [
        ("Enrique S.", 5, "Retrata a la sociedad rusa durante las guerras napoleónicas con personajes memorables como Pierre y Natasha. Larga, pero imperdible."),
        ("Clara W.", 4, "Requiere paciencia por su extensión y la cantidad de personajes, pero la recompensa es enorme. Muy buen precio para tantas páginas."),
    ],
    "saleHarryPack": [
        ("Valentina R.", 5, "Perfecto para releer la saga completa o para regalarla. Los siete libros llegaron bien protegidos dentro del estuche."),
        ("Martín C.", 5, "La mejor forma de tener toda la historia de Harry, Ron y Hermione en la biblioteca. Las ediciones de bolsillo son livianas."),
    ],
    "saleHombreFeliz": [
        ("Patricia I.", 4, "Interesante conocer la vida de Franklin en sus propias palabras, con su método de las trece virtudes."),
        ("Gustavo F.", 4, "Un clásico de la autobiografía con consejos que todavía sirven; el estilo del siglo XVIII cuesta un poco al principio."),
    ],
    "saleHP_Lovecraft": [
        ("Iván D.", 5, "Reúne relatos esenciales del horror cósmico. La edición de Valdemar es preciosa y muy completa."),
        ("Mónica B.", 4, "Atmósfera opresiva y un horror que sugiere más de lo que muestra. El estilo es denso, pero perfecto para leer de noche."),
    ],
    "saleJuegoDeTrono": [
        ("Santiago H.", 5, "Intrigas, casas nobles y una guerra por el Trono de Hierro. No hay personajes intocables, y eso mantiene la tensión."),
        ("Juliana M.", 4, "Un mundo muy trabajado. Al inicio cuesta ubicar tantas casas y nombres, pero después no puedes soltarlo."),
    ],
    "saleKobe": [
        ("Brayan S.", 5, "Kobe explica su preparación, su análisis de video y su obsesión por mejorar. Inspirador incluso si no te gusta el baloncesto."),
        ("Karen L.", 4, "Con fotos y explicaciones sobre su técnica. Es más un manual de mentalidad que una biografía tradicional."),
    ],
    "saleNikeMan": [
        ("Ernesto Z.", 5, "El fundador de Nike cuenta sus inicios vendiendo zapatillas desde el maletero de su auto. Ágil, honesta y llena de aprendizajes."),
        ("Ximena C.", 4, "Muy buena para emprendedores. Hacia el final se siente algo apresurada, pero los primeros años son fascinantes."),
    ],
    "saleObama": [
        ("Ana Cristina R.", 5, "Un relato reflexivo y sincero de su camino a la presidencia y su primer mandato. Está en inglés, pero su prosa es clara y accesible."),
        ("Miguel Á. V.", 4, "Extenso y detallado; hay capítulos muy políticos, pero las anécdotas personales lo hacen muy humano."),
    ],
    "saleOrgulloPrejuicio": [
        ("Daniela U.", 5, "Elizabeth Bennet sigue siendo una protagonista genial. Ingenio, ironía social y una historia de amor perfecta."),
        ("Fernando Y.", 4, "Lectura ligera y elegante. Al principio la sociedad de la época se siente lejana, pero engancha rápido."),
    ],
    "salePacienteSilenciosa": [
        ("Lorena Q.", 5, "Un thriller psicológico con un giro final que no vi venir. Alicia y su silencio te mantienen intrigado hasta la última página."),
        ("Jorge N.", 4, "Adictivo y de lectura rápida. Algunos elementos son algo predecibles, pero el desenlace compensa."),
    ],
    "saleQuijoje": [
        ("Rosa E.", 5, "Las aventuras de don Quijote y Sancho contra los molinos de viento siguen siendo divertidísimas y profundas."),
        ("Javier O.", 4, "Una edición manejable de un clásico enorme. Recomendable para acercarse a Cervantes sin abrumarse."),
    ],
    "saleReglonesTrocidos": [
        ("Amparo T.", 5, "Una novela intensa sobre Alice Gould, que ingresa en un psiquiátrico para investigar. Te hace dudar de quién está cuerdo."),
        ("Raúl H.", 4, "Ritmo ágil y ambientación muy lograda. Un clásico de la narrativa española del siglo XX."),
    ],
    "saleSinLimite": [
        ("Hugo L.", 3, "Tiene ideas útiles sobre motivación y comunicación, pero el tono es de autoayuda clásica y hay bastante repetición."),
        ("Yesenia P.", 2, "Esperaba más contenido práctico. Varios capítulos son motivacionales pero poco concretos."),
    ],
    "saleUlises": [
        ("Félix A.", 4, "Un reto mayúsculo: un solo día de 1904 en Dublín, siguiendo a Leopold Bloom. Hace falta paciencia y una guía de lectura."),
        ("Cecilia M.", 5, "Monumental. Cada capítulo cambia de estilo, y las notas de la edición ayudan mucho a entender las referencias."),
    ],
    "saleVagabundos": [
        ("Alexis R.", 5, "Una novela cruda y poderosa sobre Adán Santana y sus fantasmas. Mendoza retrata Bogotá y a los marginados sin adornos."),
        ("Nancy G.", 4, "Fuerte y muy bien escrita; no es una lectura ligera, pero deja huella."),
    ],
    "saleVientoNombre": [
        ("Eugenia S.", 5, "Allende entrelaza la Viena de 1938 con la frontera de Estados Unidos en la actualidad. Emotiva y muy humana."),
        ("Bruno F.", 4, "Personajes entrañables, aunque las dos historias tardan en encontrarse. Un mensaje muy actual sobre la migración."),
    ],
    "list:El olvido que seremos": [
        ("Marcela D.", 5, "Un homenaje conmovedor de Abad Faciolince a su padre, el médico Héctor Abad Gómez. Es difícil no emocionarse."),
        ("Andrés K.", 5, "Combina la memoria familiar con la violencia de Colombia. Un libro que se queda para siempre."),
    ],
    "list:La verdad sobre el caso Savolta": [
        ("Roberto S.", 4, "Una novela de la Barcelona de 1917, con conflicto obrero y corrupción. Una intriga muy bien tejida."),
        ("Elena J.", 4, "Su estructura mezcla voces, cartas y testimonios. Exige atención, pero recompensa mucho."),
    ],
    "list:Los peligros de fumar en la cama": [
        ("Pilar C.", 5, "Cuentos de terror con raíz en la realidad argentina. Inquietantes y muy bien escritos."),
        ("Tomás R.", 4, "Relatos perturbadores; algunos me dejaron pensando varios días. No son para leer antes de dormir."),
    ],
    "list:Las Venas Abiertas de América Latina (Edición 50 Aniversario)": [
        ("Carlos M.", 5, "Un clásico para entender la historia de la explotación de los recursos de la región. Prosa poderosa."),
        ("Yolanda P.", 4, "Es un ensayo con mucha postura; conviene leerlo junto con otras fuentes, pero sigue siendo influyente."),
    ],
    "list:De animales a dioses": [
        ("Manuel A.", 5, "Repasa la historia de la humanidad desde una mirada distinta: las revoluciones cognitiva, agrícola y científica. Muy sugerente."),
        ("Ingrid B.", 4, "Entretenido y lleno de ideas provocadoras, aunque algunas generalizaciones son discutibles."),
    ],
    "list:Lecciones de histeria de Colombia (Edición Bicentenario)": [
        ("Wilson T.", 5, "Una forma divertida de repasar la historia de Colombia, con humor y sin perder rigor."),
        ("Angélica F.", 4, "Ideal para quien odiaba las clases de historia. Ágil y con muchas anécdotas."),
    ],
}
