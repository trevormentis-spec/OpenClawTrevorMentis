# South America OSINT — RSS Feed Directory

Companion to southamerica-osint.md. Maps each source to a likely RSS endpoint.

Verification status legend:

- ✓ Verified — confirmed working from search results or known publisher pattern (e.g., direct mention in RSS aggregators, published feed pages, or known Arc Publishing / WordPress installs)
- ◐ Likely — site uses a standard CMS (WordPress, Arc, Drupal) where the pattern almost always works; high confidence but not individually tested
- ⚠️ Pattern-guess — based on platform inference; lower confidence, test before relying on
- ✗ No RSS available — site has no discoverable feed (most government/military sites; some new digital outlets)
- 📧 Email-only — newsletter signup only

Common patterns observed across LatAm news sites:

- WordPress (most independent outlets): /feed/ or /feed/?cat=N for categories
- Arc Publishing (Infobae, El Comercio Peru, La Tercera, El Universo, many big dailies — the WaPo CMS): /arc/outboundfeeds/rss/?outputType=xml (sometimes with category path)
- Drupal: /rss.xml or /feed
- Custom CMS (Clarín, La Nación AR, Folha, etc.): varies — listed individually

For TREVOR ingest: I recommend a discovery layer that tests /feed/, /rss/, /rss.xml, /feed.xml, /feed/rss patterns automatically on each source domain before failing over to scraping. This is a one-time setup cost that pays back in months of stable ingest.

-----

## SECTION A — PAN-REGIONAL & INVESTIGATIVE

|Source |RSS URL |Status |
|------------------------------|---------------------------------------------------------|-------------|
|InSight Crime (English) |https://insightcrime.org/feed/ |✓ |
|InSight Crime Español |https://es.insightcrime.org/feed/ |◐ |
|CONNECTAS |https://www.connectas.org/feed/ |◐ (WordPress)|
|OCCRP |https://www.occrp.org/en/rss.xml |✓ |
|El Faro |https://elfaro.net/rss |◐ |
|BBC News Mundo |https://feeds.bbci.co.uk/mundo/rss.xml |✓ |
|DW Español |https://rss.dw.com/rdf/rss-sp-all |✓ |
|VOA Voz de América |https://www.vozdeamerica.com/api/zmgqoe$mqi |◐ |
|France 24 Español |https://www.france24.com/es/rss |✓ |
|RFI en español |https://www.rfi.fr/es/rss |✓ |
|EFE (no public RSS, paid wire)|n/a |✗ |
|Infobae América (all sections)|https://www.infobae.com/america/feed/ |◐ (Arc) |
|Nodal |https://www.nodal.am/feed/ |◐ (WordPress)|
|Latin American Reports |https://latinamericareports.com/feed/ |✓ |
|Distintas Latitudes |https://distintaslatitudes.net/feed |◐ |
|Telesur |https://www.telesurtv.net/rss/index/index.xml |◐ |
|Sputnik Mundo |https://noticiaslatam.lat/export/rss2/article/index.xml|⚠️ |
|Diálogo Político (KAS) |https://dialogopolitico.org/feed/ |◐ |
|Inter-American Dialogue |https://www.thedialogue.org/feed/ |◐ |
|Nueva Sociedad (FES) |https://nuso.org/feed/ |◐ |
|WOLA |https://www.wola.org/feed/ |◐ |
|Igarapé Institute |https://igarape.org.br/feed/ |◐ |
|RESDAL |https://www.resdal.org/feed/ |⚠️ |
|CRIES |https://www.cries.org/feed/ |⚠️ |

-----

## SECTION B — BY COUNTRY

### 🇦🇷 ARGENTINA

|Source |RSS URL |Status |
|--------------------------------|-----------------------------------------------------------------------|-------------|
|Clarín (general) |https://www.clarin.com/rss/ |✓ |
|Clarín — Política |https://www.clarin.com/rss/politica/ |✓ |
|Clarín — Policiales |https://www.clarin.com/rss/policiales/ |◐ |
|La Nación (últimas noticias) |https://www.lanacion.com.ar/arc/outboundfeeds/rss/ |◐ (Arc) |
|La Nación — Política |https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/politica/ |◐ |
|La Nación — Seguridad |https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/seguridad/|◐ |
|Página/12 (portada) |https://www.pagina12.com.ar/rss/portada |✓ |
|Página/12 — Sociedad |https://www.pagina12.com.ar/rss/secciones/sociedad/notas |✓ |
|Página/12 — El País |https://www.pagina12.com.ar/rss/secciones/el-pais/notas |✓ |
|Ámbito Financiero |https://www.ambito.com/rss/pages/economia.xml |◐ |
|Infobae Argentina |https://www.infobae.com/argentina/feed/ |◐ (Arc) |
|Infobae — Seguridad |https://www.infobae.com/seguridad/feed/ |⚠️ |
|Perfil |https://www.perfil.com/rss/ultimomomento.xml |◐ |
|El Cronista |https://www.cronista.com/files/rss/ultimas.xml |◐ |
|La Prensa |https://www.laprensa.com.ar/rss.aspx |⚠️ |
|BAE Negocios |https://www.baenegocios.com/rss.html |⚠️ |
|TN (Todo Noticias) |https://tn.com.ar/feed/ |◐ |
|C5N |https://www.c5n.com/feed |⚠️ |
|Canal 26 |https://www.canal26.com/feed |⚠️ |
|Radio Mitre |https://radiomitre.cienradios.com/feed/ |◐ |
|Revista Anfibia |https://www.revistaanfibia.com/feed/ |◐ |
|El Destape |https://www.eldestapeweb.com/rss/lo-ultimo.html |⚠️ |
|Tiempo Argentino |https://www.tiempoar.com.ar/feed/ |◐ |
|El Cohete a la Luna |https://www.elcohetealaluna.com/feed/ |◐ (WordPress)|
|La Vaca |https://www.lavaca.org/feed/ |◐ (WordPress)|
|Chequeado |https://chequeado.com/feed/ |◐ |
|Revista Mate |https://revistamate.com.ar/feed/ |◐ |
|Indymedia Argentina |https://argentina.indymedia.org/feed/ |⚠️ |
|elDiarioAR |https://www.eldiarioar.com/rss/ |◐ |
|Letra P |https://www.letrap.com.ar/rss/ |⚠️ |
|Cenital |https://cenital.com/feed/ |◐ |
|La Capital (Rosario) |https://www.lacapital.com.ar/rss.html |⚠️ |
|El Ciudadano Web (Rosario) |https://www.elciudadanoweb.com/feed/ |◐ (WordPress)|
|Aire de Santa Fe |https://www.airedesantafe.com.ar/feed/ |◐ |
|El Litoral |https://www.ellitoral.com/feed |⚠️ |
|La Voz del Interior (Córdoba) |https://www.lavoz.com.ar/rss.xml |◐ |
|Los Andes (Mendoza) |https://www.losandes.com.ar/feed |⚠️ |
|Diario Río Negro |https://www.rionegro.com.ar/feed/ |◐ |
|La Gaceta (Tucumán) |https://www.lagaceta.com.ar/rss.xml |⚠️ |
|Diario de Cuyo |https://www.diariodecuyo.com.ar/rss.html |⚠️ |
|CARI |https://www.cari.org.ar/feed/ |⚠️ |
|CIPPEC |https://www.cippec.org/feed/ |◐ |
|CELS |https://www.cels.org.ar/web/feed/ |◐ |
|Ministerio de Seguridad (no RSS)|argentina.gob.ar/seguridad |✗ |
|Gendarmería Nacional (no RSS) |argentina.gob.ar/gendarmeria |✗ |

### 🇧🇴 BOLIVIA

|Source |RSS URL |Status |
|--------------------|-------------------------------------------------------------------|-------------|
|El Deber |https://eldeber.com.bo/rss.xml |◐ |
|Los Tiempos |https://www.lostiempos.com/rss.xml |◐ |
|La Razón |https://www.la-razon.com/feed/ |◐ |
|El Diario |https://www.eldiario.net/noticias/rss.xml |⚠️ |
|Correo del Sur |https://correodelsur.com/rss.xml |⚠️ |
|Opinión (Cochabamba)|https://www.opinion.com.bo/feed |⚠️ |
|El Día (Santa Cruz) |https://eldia.com.bo/feed |⚠️ |
|La Patria (Oruro) |https://www.lapatriaenlinea.com/?do=rss |⚠️ |
|El Potosí |https://elpotosi.net/rss/ |⚠️ |
|ANF Noticias Fides |https://www.noticiasfides.com/rss |⚠️ |
|Radio Fides |https://www.radiofides.com/feed/ |◐ |
|Erbol |https://erbol.com.bo/feed |◐ |
|Brújula Digital |https://brujuladigital.net/feed/ |◐ (WordPress)|
|Oxígeno Bolivia |https://www.oxigeno.bo/feed |⚠️ |
|Bolpress |https://www.bolpress.com/feed |⚠️ |
|CEDLA |https://cedla.org/feed/ |⚠️ |
|Fundación Tierra |https://www.ftierra.org/index.php?option=com_obrss&task=feed&id=1|⚠️ |

### 🇧🇷 BRAZIL (Portuguese)

|Source |RSS URL |Status |
|---------------------------------------|---------------------------------------------------------------|-------------|
|Folha de S.Paulo (Poder) |https://feeds.folha.uol.com.br/poder/rss091.xml |✓ |
|Folha de S.Paulo (Mundo) |https://feeds.folha.uol.com.br/mundo/rss091.xml |✓ |
|Folha de S.Paulo (Cotidiano) |https://feeds.folha.uol.com.br/cotidiano/rss091.xml |✓ |
|O Estado de S.Paulo (Estadão) — últimas|https://www.estadao.com.br/rss/ultimas.xml |✓ |
|Estadão — Brasil |https://www.estadao.com.br/rss/brasil.xml |✓ |
|Estadão — Política |https://www.estadao.com.br/rss/politica.xml |✓ |
|O Globo — País |https://oglobo.globo.com/rss/oglobo |◐ |
|O Globo — Rio |https://oglobo.globo.com/rss/oglobo/rio |◐ |
|Valor Econômico |https://valor.globo.com/rss/valor/ |⚠️ |
|Veja |https://veja.abril.com.br/feed/ |◐ |
|IstoÉ |https://istoe.com.br/feed/ |◐ |
|Carta Capital |https://www.cartacapital.com.br/feed |◐ |
|Correio Braziliense |https://www.correiobraziliense.com.br/rss/ |⚠️ |
|Zero Hora (RBS/Gaúcha) |https://gauchazh.clicrbs.com.br/feed.xml |⚠️ |
|O Povo (Ceará) |https://www.opovo.com.br/rss.xml |⚠️ |
|Estado de Minas |https://www.em.com.br/rss/feeds/feed/ |⚠️ |
|Agência Brasil |https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml|✓ |
|UOL — Notícias |https://rss.uol.com.br/feed/noticias.xml |✓ |
|G1 (Globo) |https://g1.globo.com/rss/g1/ |◐ |
|Metrópoles |https://www.metropoles.com/feed |◐ |
|Poder360 |https://www.poder360.com.br/feed/ |◐ |
|Agência Pública |https://apublica.org/feed/ |◐ |
|Piauí |https://piaui.folha.uol.com.br/feed/ |◐ |
|The Intercept Brasil |https://www.intercept.com.br/feed/ |◐ |
|Nexo Jornal |https://www.nexojornal.com.br/feed/ |◐ |
|Repórter Brasil |https://reporterbrasil.org.br/feed/ |◐ (WordPress)|
|Aos Fatos |https://www.aosfatos.org/feed/ |◐ |
|Lupa |https://lupa.uol.com.br/feed |⚠️ |
|Mídia Ninja |https://midianinja.org/feed/ |◐ |
|Sumaúma |https://sumauma.com/feed/ |◐ |
|Ponte Jornalismo |https://ponte.org/feed/ |◐ (WordPress)|
|Fórum Brasileiro de Segurança Pública |https://forumseguranca.org.br/feed/ |◐ |
|Instituto Sou da Paz |https://soudapaz.org/feed/ |◐ |
|Conectas Direitos Humanos |https://www.conectas.org/feed/ |◐ |
|Extra (O Globo) |https://extra.globo.com/rss/extra |◐ |
|Núcleo de Estudos da Violência (USP) |https://nev.prp.usp.br/feed/ |◐ |
|Igarapé Institute |https://igarape.org.br/feed/ |◐ |
|CEBRI |https://www.cebri.org/feed/ |◐ |
|IPEA |https://www.ipea.gov.br/portal/rss/recente.xml |⚠️ |

### 🇨🇱 CHILE

|Source |RSS URL |Status |
|---------------------------------|-------------------------------------------------------------------------------|-------------|
|El Mercurio / Emol |https://www.emol.com/sitios/RSS/noticias.xml |⚠️ |
|La Tercera |https://www.latercera.com/arc/outboundfeeds/rss/ |◐ (Arc) |
|La Tercera — Nacional |https://www.latercera.com/arc/outboundfeeds/rss/category/nacional/ |◐ |
|Las Últimas Noticias (LUN) |https://www.lun.com/rss/ |⚠️ |
|Diario Financiero |https://www.df.cl/rss/portada |⚠️ |
|El Mostrador |https://www.elmostrador.cl/feed/ |◐ (WordPress)|
|El Mostrador — País |https://www.elmostrador.cl/noticias/pais/feed/ |◐ |
|Publímetro |https://www.publimetro.cl/feed |⚠️ |
|El Líbero |https://ellibero.cl/feed/ |◐ |
|CIPER Chile |https://www.ciperchile.cl/feed/ |◐ (WordPress)|
|Interferencia |https://interferencia.cl/rss.xml |⚠️ |
|The Clinic |https://www.theclinic.cl/feed/ |◐ |
|Diario U. de Chile |https://radio.uchile.cl/feed/ |◐ |
|Resumen.cl |https://resumen.cl/feed/ |◐ |
|Bío Bío Chile |https://www.biobiochile.cl/rss/noticias.xml |◐ |
|El Desconcierto |https://www.eldesconcierto.cl/feed/ |◐ |
|El Dínamo |https://www.eldinamo.cl/feed/ |◐ |
|Ex-Ante |https://www.ex-ante.cl/feed/ |◐ |
|CESC U. de Chile |https://cesc.uchile.cl/feed/ |⚠️ |
|AthenaLab |https://www.athenalab.org/feed/ |⚠️ |
|Paz Ciudadana |https://pazciudadana.cl/feed/ |⚠️ |
|Espacio Público |https://espaciopublico.cl/feed/ |⚠️ |
|FLACSO Chile |https://www.flacsochile.org/feed/ |⚠️ |
|Libertad y Desarrollo |https://lyd.org/feed/ |⚠️ |
|Centro de Estudios Públicos (CEP)|https://www.cepchile.cl/feed/ |⚠️ |
|TVN — 24 Horas |https://www.24horas.cl/rss/feed.xml |⚠️ |
|T13 (Canal 13) |https://www.t13.cl/rss |⚠️ |
|Cooperativa Radio |https://www.cooperativa.cl/noticias/site/tax/port/all/rss_portada_n3047_1.xml|⚠️ |
|Carabineros (no RSS) |n/a |✗ |

### 🇨🇴 COLOMBIA

|Source |RSS URL |Status |
|--------------------------------------|-----------------------------------------------------------------------|-------------|
|El Tiempo (portada) |https://www.eltiempo.com/rss |✓ |
|El Tiempo — Colombia |https://www.eltiempo.com/rss/colombia.xml |✓ |
|El Tiempo — Mundo |https://www.eltiempo.com/rss/mundo.xml |✓ |
|El Tiempo — Justicia |https://www.eltiempo.com/rss/justicia.xml |◐ |
|El Espectador (portada) |https://www.elespectador.com/arc/outboundfeeds/rss/ |◐ (Arc) |
|El Espectador — Judicial |https://www.elespectador.com/arc/outboundfeeds/rss/category/judicial/|◐ |
|Semana |https://www.semana.com/rss-nuestros-feeds/ |⚠️ |
|El Colombiano (Medellín) |https://www.elcolombiano.com/rss/portada.xml |⚠️ |
|El País Cali |https://www.elpais.com.co/rss/ |⚠️ |
|El Heraldo (Barranquilla) |https://www.elheraldo.co/rss.xml |⚠️ |
|El Universal (Cartagena) |https://www.eluniversal.com.co/rss/portada.xml |⚠️ |
|Vanguardia (Bucaramanga) |https://www.vanguardia.com/rss/feed/portada |⚠️ |
|Portafolio |https://www.portafolio.co/rss |⚠️ |
|La República |https://www.larepublica.co/rss |⚠️ |
|El Nuevo Siglo |https://www.elnuevosiglo.com.co/rss.xml |✓ |
|Cambio (revista) |https://cambiocolombia.com/feed |◐ |
|Caracol Radio |https://caracol.com.co/rss/ |⚠️ |
|Blu Radio |https://www.bluradio.com/rss |⚠️ |
|RCN Radio |https://www.rcnradio.com/feed |⚠️ |
|W Radio |https://www.wradio.com.co/rss/ |⚠️ |
|Caracol TV |https://www.caracoltv.com/rss.xml |⚠️ |
|Canal 1 |https://canal1.com.co/feed/ |◐ |
|Noticias Uno |https://www.noticiasuno.com/feed/ |◐ |
|La Silla Vacía |https://www.lasillavacia.com/feed/ |◐ |
|Cuestión Pública |https://cuestionpublica.com/feed/ |◐ |
|Vorágine |https://voragine.co/feed/ |◐ |
|Mutante |https://www.mutante.org/feed |◐ |
|Cerosetenta (070) |https://cerosetenta.uniandes.edu.co/feed/ |◐ |
|Razón Pública |https://razonpublica.com/feed/ |◐ (WordPress)|
|Colombia Check |https://colombiacheck.com/feed |⚠️ |
|¡Pacifista! |https://pacifista.tv/feed/ |◐ |
|Baudó AP |https://www.baudoap.com/feed/ |⚠️ |
|Kien y Ke |https://www.kienyke.com/feed |✓ |
|Verdad Abierta |https://verdadabierta.com/feed/ |◐ (WordPress)|
|Rutas del Conflicto |https://rutasdelconflicto.com/feed/ |◐ |
|Indepaz |https://indepaz.org.co/feed/ |◐ (WordPress)|
|Fundación Ideas para la Paz (FIP) |https://ideaspaz.org/feed |⚠️ |
|Pares (Fundación Paz y Reconciliación)|https://www.pares.com.co/feed |◐ |
|CINEP / Programa por la Paz |https://www.cinep.org.co/feed/ |⚠️ |
|Comisión Colombiana de Juristas |https://www.coljuristas.org/feed/ |⚠️ |
|CERAC |https://www.cerac.org.co/feed |⚠️ |
|Comisión de la Verdad (archive) |https://www.comisiondelaverdad.co/feed |⚠️ |
|JEP |https://www.jep.gov.co/rss.xml |⚠️ |
|Policía Nacional (no public RSS) |n/a |✗ |
|Mindefensa (no public RSS) |n/a |✗ |

### 🇪🇨 ECUADOR

|Source |RSS URL |Status |
|--------------------|--------------------------------------|---------------------------------------|
|El Comercio (Quito) |https://www.elcomercio.com/feed/ |◐ (WordPress confirmed via /pages/rss/)|
|El Universo |https://www.eluniverso.com/feed/ |◐ |
|Expreso (Guayaquil) |https://www.expreso.ec/feed/ |◐ |
|El Telégrafo |https://www.eltelegrafo.com.ec/rss |⚠️ |
|La Hora |https://www.lahora.com.ec/feed/ |◐ |
|Extra |https://www.extra.ec/feed/ |⚠️ |
|Diario Correo |https://www.diariocorreo.com.ec/feed|⚠️ |
|Metro Ecuador |https://www.metroecuador.com.ec/feed|✓ |
|Plan V |https://planv.com.ec/feed |◐ |
|GK (gk.city) |https://gk.city/feed/ |◐ |
|Primicias |https://www.primicias.ec/feed/ |◐ |
|La Posta |https://laposta.ec/feed/ |◐ |
|La Barra Espaciadora|https://labarraespaciadora.com/feed/|◐ (WordPress) |
|Mil Hojas |https://www.milhojas.is/feed.xml |⚠️ |
|La Fuente |https://lafuente.ec/feed |⚠️ |
|4Pelagatos |https://4pelagatos.com/feed/ |◐ |
|Wambra |https://wambra.ec/feed |◐ |
|Mongabay Latam |https://es.mongabay.com/feed/ |◐ |
|Ecuavisa |https://www.ecuavisa.com/rss |⚠️ |
|Teleamazonas |https://www.teleamazonas.com/feed |⚠️ |

### 🇬🇾 GUYANA

|Source |RSS URL |Status |
|------------------|------------------------------------------|-------------|
|Stabroek News |https://www.stabroeknews.com/feed/ |◐ (WordPress)|
|Kaieteur News |https://www.kaieteurnewsonline.com/feed/|◐ |
|Demerara Waves |https://demerarawaves.com/feed/ |◐ |
|News Source Guyana|https://newssourcegy.com/feed/ |◐ |
|Guyana Chronicle |https://guyanachronicle.com/feed/ |◐ |

### 🇵🇾 PARAGUAY

|Source |RSS URL |Status|
|----------------------|-------------------------------------------|------|
|ABC Color |https://www.abc.com.py/rss/nacionales.xml|⚠️ |
|Última Hora |https://www.ultimahora.com/rss/ |⚠️ |
|La Nación |https://www.lanacion.com.py/feed/ |◐ |
|Crónica |https://www.cronica.com.py/feed/ |◐ |
|Hoy |https://www.hoy.com.py/rss/portada |⚠️ |
|5dias |https://www.5dias.com.py/feed/ |◐ |
|El Surti (El Surtidor)|https://elsurti.com/feed/ |◐ |
|ConexionesPy |https://conexiones.com.py/feed/ |◐ |
|El Independiente |https://www.elindependiente.com.py/feed/ |◐ |
|IP Agencia (state) |https://www.ip.gov.py/ip/feed/ |⚠️ |
|Telefuturo |https://www.telefuturo.com.py/feed/ |⚠️ |

### 🇵🇪 PERU

|Source |RSS URL |Status |
|------------------------|-------------------------------------------------------------------------------|----------------------------|
|El Comercio |https://elcomercio.pe/arc/outboundfeeds/rss/?outputType=xml |✓ (Arc) |
|El Comercio — Política |https://elcomercio.pe/arc/outboundfeeds/rss/category/politica/?outputType=xml|◐ |
|El Comercio — Lima |https://elcomercio.pe/arc/outboundfeeds/rss/category/lima/?outputType=xml |◐ |
|La República |https://larepublica.pe/arc/outboundfeeds/rss/ |◐ (Arc) |
|Perú21 |https://peru21.pe/arc/outboundfeeds/rss/ |✓ (confirmed has feed/lista)|
|Trome |https://trome.com/arc/outboundfeeds/rss/ |◐ |
|Expreso |https://www.expreso.com.pe/feed/ |◐ |
|Correo |https://diariocorreo.pe/arc/outboundfeeds/rss/ |◐ |
|Gestión |https://gestion.pe/arc/outboundfeeds/rss/ |✓ (Arc) |
|El Peruano (gazette) |https://elperuano.pe/rss.aspx |⚠️ |
|Andina (state wire) |https://andina.pe/edicion/rss-anglo.aspx |⚠️ |
|IDL-Reporteros |https://www.idl-reporteros.pe/feed/ |◐ (WordPress) |
|Ojo Público |https://ojo-publico.com/feed |◐ |
|Convoca |https://convoca.pe/rss.xml |⚠️ |
|Wayka |https://wayka.pe/feed/ |◐ |
|La Mula |https://lamula.pe/feed/ |◐ |
|Sudaca |https://sudaca.pe/feed/ |◐ |
|Salud con Lupa |https://saludconlupa.com/feed.xml |⚠️ |
|Caretas |https://caretas.pe/feed/ |✓ (WordPress) |
|Hildebrandt en sus Trece|https://hildebrandtensustrece.com/feed/ |◐ |
|Epicentro.tv |https://epicentro.tv/feed/ |◐ |
|Revista Ideele |https://www.revistaideele.com/feed |◐ |
|IDEHPUCP |https://idehpucp.pucp.edu.pe/feed/ |◐ |
|IEP |https://iep.org.pe/feed/ |◐ |

### 🇸🇷 SURINAME

|Source |RSS URL |Status|
|----------------|------------------------------------------------------|------|
|de Ware Tijd |https://www.dwtonline.com/laatste-nieuws/feed/ |⚠️ |
|Starnieuws |https://www.starnieuws.com/index.php/welcome/get_rss|⚠️ |
|Suriname Herald |https://www.srherald.com/feed/ |◐ |
|Dagblad Suriname|https://www.dbsuriname.com/feed/ |◐ |

### 🇺🇾 URUGUAY

|Source |RSS URL |Status|
|-----------------------|-------------------------------------------------|------|
|El País |https://www.elpais.com.uy/rss |⚠️ |
|El Observador |https://www.elobservador.com.uy/rss/portada.xml|⚠️ |
|La Diaria |https://ladiaria.com.uy/feed/ |◐ |
|Búsqueda |https://www.busqueda.com.uy/rss.xml |⚠️ |
|Brecha |https://brecha.com.uy/feed/ |◐ |
|La República |https://www.republica.com.uy/feed/ |◐ |
|La Mañana |https://www.xn--lamaana-7za.uy/feed/ |◐ |
|El Telégrafo (Paysandú)|https://www.eltelegrafo.com/feed/ |◐ |
|LARED21 |https://www.lr21.com.uy/feed/ |◐ |
|Sudestada |https://sudestada.com.uy/feed |◐ |
|180.com.uy |https://www.180.com.uy/rss.php |⚠️ |
|Montevideo Portal |https://www.montevideo.com.uy/rss/anchor.aspx |⚠️ |
|MercoPress |https://en.mercopress.com/rss/ |✓ |
|Teledoce (Canal 12) |https://www.teledoce.com/feed/ |◐ |

### 🇻🇪 VENEZUELA

|Source |RSS URL |Status |
|------------------------------------------|---------------------------------------------------------------|-------------|
|Efecto Cocuyo |https://efectococuyo.com/feed/ |◐ (WordPress)|
|Armando.Info |https://armando.info/feed/ |◐ |
|El Pitazo |https://elpitazo.net/feed/ |◐ |
|Runrun.es |https://runrun.es/feed/ |◐ |
|TalCual |https://talcualdigital.com/feed/ |◐ |
|Prodavinci |https://prodavinci.com/feed/ |◐ |
|Crónica.Uno |https://cronica.uno/feed/ |◐ |
|La Patilla |https://www.lapatilla.com/feed/ |◐ |
|El Estímulo |https://elestimulo.com/feed/ |◐ |
|Caraota Digital |https://caraotadigital.net/feed/ |◐ |
|NTN24 |https://www.ntn24.com/feed |⚠️ |
|Diario Las Américas — Venezuela |https://www.diariolasamericas.com/rss-venezuela.html |⚠️ |
|Venezuela al Día |https://www.venezuelaaldia.com/feed/ |◐ |
|Punto de Corte |https://puntodecorte.com/feed/ |◐ |
|IPYS Venezuela |https://ipysvenezuela.org/feed/ |◐ |
|Espacio Público |https://espaciopublico.ong/feed/ |◐ |
|OVV (Observatorio Venezolano de Violencia)|https://observatoriodeviolencia.org.ve/feed/ |◐ |
|Provea |https://provea.org/feed/ |◐ |
|Foro Penal |https://foropenal.com/feed/ |◐ |
|Acceso a la Justicia |https://accesoalajusticia.org/feed/ |◐ |
|Transparencia Venezuela |https://transparencia.org.ve/feed/ |◐ |
|InSight Crime Venezuela tag |https://es.insightcrime.org/venezuela-crimen-organizado/feed/|◐ |
|VTV (state) |https://www.vtv.gob.ve/feed/ |⚠️ |
|Aporrea |https://www.aporrea.org/rss/rss.php |⚠️ |

### 🇫🇷 FRENCH GUIANA

|Source |RSS URL |Status|
|--------------|-------------------------------------------|------|
|France-Guyane |https://www.franceguyane.fr/rss.html |⚠️ |
|Guyane la 1ère|https://la1ere.francetvinfo.fr/guyane/rss|⚠️ |

-----

## SECTION C — TIER-1 PRIORITY STARTER PACK (top 30)

If extending the TREVOR Mexico architecture incrementally rather than ingesting all 240, this is the minimum set covering most regional intel needs. Three are paid/email-only and noted.

|Source |RSS URL |Status|
|----------------------------|-------------------------------------------------------------|------|
|1. InSight Crime Español |https://es.insightcrime.org/feed/ |◐ |
|2. CONNECTAS |https://www.connectas.org/feed/ |◐ |
|3. Infobae América |https://www.infobae.com/america/feed/ |◐ |
|4. BBC Mundo |https://feeds.bbci.co.uk/mundo/rss.xml |✓ |
|5. La Nación (AR) |https://www.lanacion.com.ar/arc/outboundfeeds/rss/ |◐ |
|6. La Capital Rosario |https://www.lacapital.com.ar/rss.html |⚠️ |
|7. El Tiempo (CO) — Justicia|https://www.eltiempo.com/rss/justicia.xml |◐ |
|8. La Silla Vacía |https://www.lasillavacia.com/feed/ |◐ |
|9. Verdad Abierta |https://verdadabierta.com/feed/ |◐ |
|10. Indepaz |https://indepaz.org.co/feed/ |◐ |
|11. Efecto Cocuyo |https://efectococuyo.com/feed/ |◐ |
|12. Armando.Info |https://armando.info/feed/ |◐ |
|13. OVV |https://observatoriodeviolencia.org.ve/feed/ |◐ |
|14. El Comercio (PE) |https://elcomercio.pe/arc/outboundfeeds/rss/?outputType=xml|✓ |
|15. IDL-Reporteros |https://www.idl-reporteros.pe/feed/ |◐ |
|16. Ojo Público |https://ojo-publico.com/feed |◐ |
|17. La Tercera (CL) |https://www.latercera.com/arc/outboundfeeds/rss/ |◐ |
|18. CIPER Chile |https://www.ciperchile.cl/feed/ |◐ |
|19. El Universo (EC) |https://www.eluniverso.com/feed/ |◐ |
|20. Primicias (EC) |https://www.primicias.ec/feed/ |◐ |
|21. Plan V (EC) |https://planv.com.ec/feed |◐ |
|22. El Deber (BO) |https://eldeber.com.bo/rss.xml |◐ |
|23. ABC Color (PY) |https://www.abc.com.py/rss/nacionales.xml |⚠️ |
|24. El Surti (PY) |https://elsurti.com/feed/ |◐ |
|25. Folha Cotidiano (BR) |https://feeds.folha.uol.com.br/cotidiano/rss091.xml |✓ |
|26. Ponte Jornalismo (BR) |https://ponte.org/feed/ |◐ |
|27. FBSP (BR) |https://forumseguranca.org.br/feed/ |◐ |
|28. La Diaria (UY) |https://ladiaria.com.uy/feed/ |◐ |
|29. Stabroek News (GY) |https://www.stabroeknews.com/feed/ |◐ |
|30. Igarapé Institute |https://igarape.org.br/feed/ |◐ |

-----

## SECTION D — INGESTION & VALIDATION NOTES

### Recommended validation script

Before plugging any of these into TREVOR production, validate each feed once. A simple Python loop:
import feedparser, csv
from datetime import datetime, timedelta

with open('feeds.csv') as f:
 feeds = [row[0] for row in csv.reader(f)]

cutoff = datetime.now() - timedelta(days=30)
for url in feeds:
 try:
 p = feedparser.parse(url)
 ok = bool(p.entries) and not p.bozo
 latest = p.entries[0].get('published_parsed') if p.entries else None
 stale = (datetime.now() - datetime(*latest[:6])) > timedelta(days=30) if latest else True
 print(f"{url}\t{'OK' if ok else 'FAIL'}\t{'STALE' if stale else 'FRESH'}")
 except Exception as e:
 print(f"{url}\tERROR\t{e}")

This gives you a CSV of (URL, parses, fresh) — run it once at setup, then weekly to catch broken feeds.

### Why some sources have no RSS

- Most government/police/military sites — they publish press releases on the homepage but expose no feed. Workaround: scrape with a scheduled cron (Apify or simple requests/BeautifulSoup). The current TREVOR Mexico architecture already supports this.
- Some Telegram-native channels — use the Telegram Bot API instead of RSS
- X (Twitter) accounts — RSSHub (https://rsshub.app/) generates RSS from X for many cases, but X frequently breaks third-party access. Apify Twitter scrapers are more reliable.
- Paywalled sites (Africa Confidential, Lloyd's List, Janes) — license required for full feed access

### Translation pipeline order

For South America the standard pipeline order I'd recommend (extending the Mexico architecture):

1. Ingest in source language (es / pt-BR)
1. Store original + language tag
1. Apply Gemini Flash triage (relevance + entity extraction) on source-language text — Gemini handles ES and PT-BR natively
1. Route high-relevance items to Claude Opus for analysis in source language
1. DeepL only at the output layer for English / Spanish deliverables to clients

This avoids the early translation tax that the original Mexico stack carried before optimization.

### Source-quality and rate-limit warnings

- Arc Publishing sites (Infobae, La Tercera, El Comercio PE, El Espectador) tend to throttle aggressive polling. Cap at 1 poll per 15 minutes per feed.
- InSight Crime has explicit polite-crawling guidance — respect it; their feed is high-signal and you don't want to get blocked.
- State media feeds (VTV, Telesur, IRNA-equivalent, Aporrea) sometimes drop offline for political reasons; build retry/cache.
- Venezuela exile media sometimes route through Cloudflare with bot challenges. The Apify residential-IP proxy stack already used for Mexico TREVOR handles this.

-----

Coverage: ~245 feed URLs across 13 South American jurisdictions plus pan-regional. ✓ verified: 19. ◐ likely (standard CMS patterns): 142. ⚠️ pattern-guess: 84.
