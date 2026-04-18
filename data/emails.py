"""
Correos ficticios para el PoC de automatización de gestión de conciertos.
Cada correo tiene un formato, idioma y nivel de completitud diferente.
"""

CORREUS = [
    {
        "id": 1,
        "de": "cultura@ajuntament.tortosa.cat",
        "assumpte": "Contratación actuación Fiesta Mayor 2026",
        "cos": """Buenas tardes,

Me pongo en contacto con vosotros en representación del Ayuntamiento de Tortosa.
Estamos organizando nuestra Fiesta Mayor y nos gustaría contar con vuestra
actuación el próximo 15 de agosto de 2026 en el Parque de Sant Antoni (capacidad
para unas 800 personas).

El aforo del espacio es de 800 personas y el presupuesto destinado a la actuación
es de 3.000 euros (IVA incluido).

¿Podéis indicarnos vuestra disponibilidad y condiciones?

Muchas gracias,
Marta Solà
Concejalía de Cultura
Ayuntamiento de Tortosa
""",
    },
    {
        "id": 2,
        "de": "pepe.garcia@gmail.com",
        "assumpte": "concierto para mi bar",
        "cos": """hola! os escribo porque queremos organizar un concierto en nuestro bar,
el Bar El Racó, que está en Lleida. Tenemos capacidad para unas 60 personas
y nos gustaría algo para finales de junio o principios de julio, sin fecha
concreta todavía.

¿cuánto cobráis más o menos?

gracias
pepe
""",
    },
    {
        "id": 3,
        "de": "events@castelldefels-cultura.org",
        "assumpte": "Solicitud de actuación musical - Festival de Verano",
        "cos": """Estimado equipo,

Estamos organizando el Festival de Música de Verano de Castelldefels y nos
gustaría invitaros a actuar el 22 de julio de 2026.

El evento tendrá lugar en el Auditorio Municipal de Castelldefels, con un
aforo previsto de 400 personas. Nuestro presupuesto para esta actuación
es de 2.500 EUR.

Por favor, indicadnos vuestra disponibilidad y enviadnos vuestro rider técnico.

Un saludo,
Laura Puig
Coordinadora de Eventos
Fundación Cultural de Castelldefels
""",
    },
    {
        "id": 4,
        "de": "associacio.veins.gracia@gmail.com",
        "assumpte": "concierto en el barrio",
        "cos": """¡Hola!

Somos la asociación de vecinos del barrio de Gràcia de Barcelona y queremos
organizar un concierto en la calle para la Fiesta Mayor de Gràcia. Sería en
la Plaza del Sol.

Todavía no sabemos bien las fechas pero sería durante la semana de la fiesta
mayor (normalmente la tercera semana de agosto).

¿Cuánto costaría? ¿Y qué amplificación traéis?

¡Gracias!
""",
    },
    {
        "id": 5,
        "de": "direccio@espaciocultural-zaragoza.es",
        "assumpte": "Propuesta actuación otoño 2026",
        "cos": """Buenos días,

Desde el Espacio Cultural La Llave de Zaragoza nos ponemos en contacto
para solicitar presupuesto para una actuación el 3 de octubre de 2026.

Nuestro aforo es de 250 personas. Lamentablemente no disponemos de
presupuesto confirmado todavía, ya que estamos pendientes de una
subvención del Ayuntamiento.

¿Podríais enviarnos vuestra tarifa orientativa?

Atentamente,
Roberto Fuentes
Director Artístico
Espacio Cultural La Llave
""",
    },
    # ─── Nous correus ─────────────────────────────────────────────────────────
    {
        "id": 6,
        "de": "culture@association-perpignan.fr",
        "assumpte": "Demande de concert - Festival d'Automne de Perpignan",
        "cos": """Bonjour,

L'Association Culturelle de Perpignan vous contacte afin d'organiser un concert
dans notre salle polyvalente le 15 septembre 2026. Notre salle dispose d'une
capacité de 350 personnes et nous avons prévu un budget de 2.000 euros pour
cette soirée musicale.

Pourriez-vous nous confirmer votre disponibilité et nous faire parvenir votre
fiche technique ?

Cordialement,
Marie Dupont
Association Culturelle de Perpignan
""",
    },
    {
        "id": 7,
        "de": "cultura@centrecultural-girona.cat",
        "assumpte": "Invitació per al Cicle de Música d'Estiu 2026",
        "cos": """Benvolguts,

Des del Centre Cultural de Girona us volem convidar a actuar en el nostre
Cicle de Música d'Estiu el proper 21 de juny de 2026. L'aforament de la sala
és de 220 persones i disposem d'un pressupost de 1.800 euros per a l'actuació.

Si us plau, confirmeu-nos la vostra disponibilitat i envieu-nos el vostre rider tècnic.

Moltes gràcies,
Josep Roca
Coordinador de Programació
Centre Cultural de Girona
""",
    },
    {
        "id": 8,
        "de": "booking@barcelonaartsfestival.com",
        "assumpte": "Performance Request - Barcelona Arts Festival 2026",
        "cos": """Hello,

We are reaching out on behalf of the Barcelona Arts Festival to inquire about
your availability for a live performance on July 5th, 2026. The event will take
place at the Palau de la Música in Barcelona, with an expected audience of 600
people. Our budget for the performance is 4.000 EUR.

Please let us know your availability and send us your technical rider.

Best regards,
Sarah Johnson
Booking Manager
Barcelona Arts Festival
""",
    },
    {
        "id": 9,
        "de": "cultura@ajuntament.reus.cat",
        "assumpte": "Sol·licitud actuació Fira de Tardor de Reus 2026",
        "cos": """Benvolguts,

La Regidoria de Cultura de l'Ajuntament de Reus us convida a participar en la
Fira de Tardor 2026, el proper 14 de novembre de 2026. L'acte tindrà lloc a la
Plaça del Mercadal, amb un aforament de 500 persones.

Disposem d'un pressupost de 3.500 euros i la durada prevista de l'actuació
és de 2 hores. Agrairíem que ens confirmeu disponibilitat i rider tècnic.

Atentament,
Carmen Martí
Ajuntament de Reus
""",
    },
    {
        "id": 10,
        "de": "david.valls@escolamusica-manresa.cat",
        "assumpte": "Concert de reencuentro - Escola de Música de Manresa",
        "cos": """Hola,

Somos la Asociación de Antiguos Alumnos de la Escola de Música de Manresa y
queremos organizar un concierto de reencuentro para el verano de 2026, aunque
todavía no hemos decidido la fecha exacta.

El evento se celebraría en el auditorio de Manresa, con aforo para unas 150
personas. El presupuesto disponible es de 1.200 euros.

¿Podríais enviarnos información sobre vuestras condiciones?

Gracias,
David Valls
Asociación de Antiguos Alumnos
Escola de Música de Manresa
""",
    },
    {
        "id": 11,
        "de": "info@fundaciosolidaritat.org",
        "assumpte": "Actuació musical per a sopar benèfic",
        "cos": """Hola,

Ens posem en contacte des de la Fundació Solidaritat per demanar-vos disponibilitat
per a una actuació el 25 d'abril de 2026. Organitzem un sopar benèfic anual però
encara no hem confirmat el restaurant on es farà, ja que estem en negociació
amb diversos espais.

L'aforament previst és d'unes 120 persones i tenim un pressupost de 1.000 euros.

Moltes gràcies per la vostra atenció,
Núria Pons
Fundació Solidaritat
""",
    },
    {
        "id": 12,
        "de": "service.culture@mairie-montpellier.fr",
        "assumpte": "Invitation festival d'été - Mairie de Montpellier",
        "cos": """Bonjour,

La mairie de Montpellier organise son grand festival d'été et souhaite vous inviter
à vous produire. Nous n'avons pas encore arrêté les dates précises du programme,
mais ce serait courant juillet ou août 2026. La capacité du site est de 1.000
personnes et nous avons un budget de 3.500 euros pour cette prestation.

Nous reviendrons vers vous dès que les dates seront fixées.

Cordialement,
François Martin
Service Culturel - Mairie de Montpellier
""",
    },
    {
        "id": 13,
        "de": "ana.garcia@gmail.com",
        "assumpte": "Consulta disponibilitat 12 de maig",
        "cos": """Buenos días,

Me llamo Ana García y os escribo para consultar vuestra disponibilidad el
12 de mayo de 2026 en Sabadell. Estamos planificando algo pero todavía no
sabemos exactamente qué formato tendría el acto, ya que estamos valorando
varias opciones.

Seríamos unas 80 personas. ¿Cuáles son vuestras tarifas?

Gracias,
Ana García
""",
    },
    {
        "id": 14,
        "de": "events@clubesportiu-sants.cat",
        "assumpte": "Gala anual Club Esportiu Sants-Montjuïc",
        "cos": """Buenas tardes,

El Club Deportivo Sants-Montjuïc organiza su gala anual de reconocimientos el
próximo 22 de agosto de 2026 en el Pavelló Municipal de Sants-Montjuïc, con
capacidad para 300 personas.

Nos gustaría contar con una actuación musical en directo. Nuestro presupuesto
para la velada es de 2.200 euros.

¿Podéis confirmar vuestra disponibilidad?

Un saludo,
Jordi Ferrer
Club Deportiu Sants-Montjuïc
""",
    },
    {
        "id": 15,
        "de": "events@hotelpalaudemar.com",
        "assumpte": "Actuació musical Festa de Cap d'Any 2026",
        "cos": """Bon dia,

L'Hotel Palau de Mar de Barcelona organitza una gran festa de Cap d'Any el
31 de desembre de 2026 i volíem contractar una actuació musical en directe
per amenitzar la vetllada. L'aforament de la sala de gala és de 180 persones
i disposem d'un pressupost de 2.800 euros per a l'actuació.

Podeu confirmar-nos disponibilitat per a aquesta data?

Moltes gràcies,
Laia Ribas
Directora d'Esdeveniments
Hotel Palau de Mar
""",
    },
    {
        "id": 16,
        "de": "info@restaurantelmolibarcelona.com",
        "assumpte": "Actuació musical sopar de Nadal 25 desembre",
        "cos": """Hola,

Desde el Restaurante El Molí de Barcelona nos gustaría organizar una cena
especial de Navidad el 25 de diciembre de 2026 con actuación musical en directo.
El restaurante tiene capacidad para unas 60 personas y el presupuesto disponible
para la actuación es de 1.500 euros.

¿Estaríais disponibles para esta fecha?

Gracias,
Miquel Torres
Restaurante El Molí
""",
    },
    {
        "id": 17,
        "de": "cultura@ajuntament.vilafranca.cat",
        "assumpte": "Invitació Fira de la Música - Vilafranca del Penedès 2026",
        "cos": """Benvolguts,

L'Ajuntament de Vilafranca del Penedès us convida a participar en la nostra
Fira de la Música el proper 20 de maig de 2026. L'actuació tindria lloc a la
Plaça de la Vila, amb aforament per a 1.000 persones.

El pressupost destinat per a l'actuació és de 4.500 euros i la durada prevista
és d'1 hora i 30 minuts.

Esperem la vostra resposta,
Montserrat Cortès
Regidoria de Cultura
Ajuntament de Vilafranca del Penedès
""",
    },
    {
        "id": 18,
        "de": "michael.brown@email.com",
        "assumpte": "Private concert inquiry",
        "cos": """Hello,

I'm organizing a small private concert and I'd like to know about your availability
and fees. The event would host around 40 people and our budget is approximately
600 EUR. We haven't yet decided on the date or the venue, as we are still in the
planning stages.

Could you please send me your availability calendar and pricing information?

Best regards,
Michael Brown
""",
    },
    {
        "id": 19,
        "de": "direccio@fundacioarte-zaragoza.es",
        "assumpte": "Gala d'Inauguració - Fundació Arte Contemporáneo de Zaragoza",
        "cos": """Buenos días,

La Fundación Arte Contemporáneo de Zaragoza os contacta para solicitar una
actuación musical en nuestra gala de inauguración el próximo 3 de octubre de 2026.
La gala se celebrará en el Auditorio de Zaragoza, con un aforo de 450 personas
y un presupuesto de 3.800 euros.

Agradecemos vuestra pronta respuesta.

Saludos cordiales,
Elena Ruiz
Directora Ejecutiva
Fundación Arte Contemporáneo de Zaragoza
""",
    },
    {
        "id": 20,
        "de": "info1847263@protonmail.com",
        "assumpte": "Concert de jazz al carrer a Vic",
        "cos": """Hola,

Us escric per preguntar sobre la vostra disponibilitat per a un concert de jazz
al carrer el 18 de setembre de 2026 a Vic.

Gràcies per la vostra atenció.
""",
    },
]
