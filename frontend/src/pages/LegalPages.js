import React from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { useLanguage, SUPPORTED } from '../i18n/LanguageContext';
import LanguageSwitcher from '../components/LanguageSwitcher';
import SEOHead from '../components/SEOHead';

const CO = {
  legal: 'NeXify Automate', ceo: 'Pascal Courbois, Geschäftsführer (Directeur)',
  nl: 'Graaf van Loonstraat 1E, 5921 JA Venlo, Niederlande',
  de: 'Wallstraße 9, 41334 Nettetal-Kaldenkirchen, Deutschland',
  phone: '+31 6 133 188 56', email: 'support@nexify-automate.com',
  web: 'nexify-automate.com', kvk: '90483944', vat: 'NL865786276B01'
};

const BACK = { de: 'Zurück zur Startseite', nl: 'Terug naar de startpagina', en: 'Back to homepage' };

const LegalWrap = ({ children, title }) => {
  const { lang } = useLanguage();
  return (
    <div className="legal-page">
      <SEOHead lang={lang} page="legal" />
      <nav className="legal-nav">
        <div className="legal-nav-inner">
          <a href={`/${lang}`} className="legal-logo-link">
            <img src="/icon-mark.svg" alt="" width="28" height="28" />
            <span className="legal-logo-text">NeXify<span className="legal-logo-accent">AI</span></span>
          </a>
          <span className="legal-tagline">Chat it. Automate it.</span>
          <LanguageSwitcher />
        </div>
        <a href={`/${lang}`} className="legal-back">&larr; {BACK[lang] || BACK.en}</a>
      </nav>
      <main className="legal-content"><h1>{title}</h1>{children}</main>
    </div>
  );
};

/* ═══════════ IMPRESSUM ═══════════ */
const ImpressumContent = {
  de: () => (
    <>
      <section><h2>Angaben gemäß Art. 3:15d Burgerlijk Wetboek (BW), § 5 TMG und Art. 5 ECG</h2><p><strong>{CO.legal}</strong><br/>(Eenmanszaak, eingetragen bei der Kamer van Koophandel)</p><p><strong>Hauptsitz (Niederlande):</strong><br/>{CO.nl}</p><p><strong>Niederlassung (Deutschland):</strong><br/>{CO.de}</p></section>
      <section><h2>Vertreten durch</h2><p>{CO.ceo}</p></section>
      <section><h2>Kontakt</h2><p>Telefon: <a href={`tel:${CO.phone.replace(/\s/g,'')}`}>{CO.phone}</a><br/>E-Mail: <a href={`mailto:${CO.email}`}>{CO.email}</a><br/>Web: <a href={`https://${CO.web}`} target="_blank" rel="noopener noreferrer">{CO.web}</a></p></section>
      <section><h2>Handelsregister</h2><p>Kamer van Koophandel (KvK-Nummer): {CO.kvk}<br/>Umsatzsteuer-Identifikationsnummer (BTW-ID): {CO.vat}</p><p>Hinweis: {CO.legal} ist als niederländisches Unternehmen im Handelsregister der Kamer van Koophandel eingetragen. Der deutsche Standort dient als Niederlassung für den DACH-Markt.</p></section>
      <section><h2>Verantwortlich für den Inhalt</h2><p>Pascal Courbois<br/>{CO.nl}</p><p>Verantwortlich gemäß § 18 Abs. 2 Medienstaatsvertrag (MStV) für journalistisch-redaktionelle Inhalte.</p></section>
      <section><h2>Anwendbares Recht</h2><p>Auf {CO.legal} als niederländisches Unternehmen findet grundsätzlich niederländisches Recht Anwendung, insbesondere das Burgerlijk Wetboek (BW). Für Verbraucher im DACH-Raum bleiben die zwingenden Verbraucherschutzvorschriften ihres jeweiligen Wohnsitzstaates unberührt (Art. 6 Abs. 2 Rom-I-Verordnung).</p></section>
      <section><h2>EU-Streitschlichtung</h2><p>Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: <a href="https://ec.europa.eu/consumers/odr/" target="_blank" rel="noopener noreferrer">https://ec.europa.eu/consumers/odr/</a></p><p>Wir sind weder bereit noch verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p></section>
      <section><h2>Haftungshinweis</h2><p>Die Inhalte dieser Website wurden mit größter Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität übernehmen wir keine Gewähr. Gemäß Art. 6:196c BW sind wir als Diensteanbieter für eigene Informationen verantwortlich, jedoch nicht verpflichtet, übermittelte oder gespeicherte Informationen Dritter aktiv zu überwachen.</p></section>
      <section><h2>Urheberrecht</h2><p>Alle Inhalte, Grafiken und Texte auf dieser Website unterliegen dem Urheberrecht von {CO.legal} bzw. der jeweiligen Rechteinhaber.</p></section>
      <p className="legal-date">Stand: April 2026</p>
    </>
  ),
  nl: () => (
    <>
      <section><h2>Gegevens conform Art. 3:15d Burgerlijk Wetboek (BW)</h2><p><strong>{CO.legal}</strong><br/>(Eenmanszaak, ingeschreven bij de Kamer van Koophandel)</p><p><strong>Hoofdkantoor (Nederland):</strong><br/>{CO.nl}</p><p><strong>Vestiging (Duitsland):</strong><br/>{CO.de}</p></section>
      <section><h2>Vertegenwoordigd door</h2><p>{CO.ceo}</p></section>
      <section><h2>Contact</h2><p>Telefoon: <a href={`tel:${CO.phone.replace(/\s/g,'')}`}>{CO.phone}</a><br/>E-mail: <a href={`mailto:${CO.email}`}>{CO.email}</a><br/>Web: <a href={`https://${CO.web}`} target="_blank" rel="noopener noreferrer">{CO.web}</a></p></section>
      <section><h2>Handelsregister</h2><p>Kamer van Koophandel (KvK-nummer): {CO.kvk}<br/>BTW-identificatienummer: {CO.vat}</p><p>{CO.legal} is als Nederlands bedrijf ingeschreven bij de Kamer van Koophandel. De Duitse vestiging dient als kantoor voor de DACH-markt.</p></section>
      <section><h2>Verantwoordelijk voor de inhoud</h2><p>Pascal Courbois<br/>{CO.nl}</p></section>
      <section><h2>Toepasselijk recht</h2><p>Op {CO.legal} als Nederlands bedrijf is Nederlands recht van toepassing, in het bijzonder het Burgerlijk Wetboek (BW). Voor consumenten in de DACH-regio blijven de dwingende consumentenbeschermingsregels van hun woonplaats onverlet (Art. 6 lid 2 Rome I-verordening).</p></section>
      <section><h2>EU-Geschillenbeslechting</h2><p>De Europese Commissie biedt een platform voor online geschillenbeslechting (ODR): <a href="https://ec.europa.eu/consumers/odr/" target="_blank" rel="noopener noreferrer">https://ec.europa.eu/consumers/odr/</a></p></section>
      <section><h2>Aansprakelijkheid</h2><p>De inhoud van deze website is met de grootst mogelijke zorg samengesteld. Voor de juistheid, volledigheid en actualiteit aanvaarden wij geen aansprakelijkheid. Conform Art. 6:196c BW zijn wij als dienstverlener verantwoordelijk voor eigen informatie.</p></section>
      <section><h2>Auteursrecht</h2><p>Alle inhoud, afbeeldingen en teksten op deze website vallen onder het auteursrecht van {CO.legal}.</p></section>
      <p className="legal-date">Status: april 2026</p>
    </>
  ),
  en: () => (
    <>
      <section><h2>Information pursuant to Art. 3:15d Dutch Civil Code (BW), § 5 TMG and Art. 5 ECG</h2><p><strong>{CO.legal}</strong><br/>(Eenmanszaak, registered with the Dutch Chamber of Commerce)</p><p><strong>Headquarters (Netherlands):</strong><br/>{CO.nl}</p><p><strong>Branch Office (Germany):</strong><br/>{CO.de}</p></section>
      <section><h2>Represented by</h2><p>{CO.ceo}</p></section>
      <section><h2>Contact</h2><p>Phone: <a href={`tel:${CO.phone.replace(/\s/g,'')}`}>{CO.phone}</a><br/>Email: <a href={`mailto:${CO.email}`}>{CO.email}</a><br/>Web: <a href={`https://${CO.web}`} target="_blank" rel="noopener noreferrer">{CO.web}</a></p></section>
      <section><h2>Trade Register</h2><p>Chamber of Commerce (KvK number): {CO.kvk}<br/>VAT identification number (BTW-ID): {CO.vat}</p><p>{CO.legal} is registered as a Dutch company with the Chamber of Commerce. The German location serves as a branch office for the DACH market.</p></section>
      <section><h2>Responsible for content</h2><p>Pascal Courbois<br/>{CO.nl}</p></section>
      <section><h2>Applicable law</h2><p>Dutch law applies to {CO.legal} as a Dutch company, in particular the Burgerlijk Wetboek (BW). For consumers in the DACH region, the mandatory consumer protection provisions of their respective country of residence remain unaffected (Art. 6(2) Rome I Regulation).</p></section>
      <section><h2>EU Dispute Resolution</h2><p>The European Commission provides a platform for online dispute resolution (ODR): <a href="https://ec.europa.eu/consumers/odr/" target="_blank" rel="noopener noreferrer">https://ec.europa.eu/consumers/odr/</a></p></section>
      <section><h2>Liability Notice</h2><p>The content of this website has been created with the utmost care. We accept no liability for its accuracy, completeness or timeliness. Pursuant to Art. 6:196c BW, we are responsible for our own information as a service provider.</p></section>
      <section><h2>Copyright</h2><p>All content, graphics and texts on this website are protected by copyright of {CO.legal} or the respective rights holders.</p></section>
      <p className="legal-date">Last updated: April 2026</p>
    </>
  )
};

/* ═══════════ DATENSCHUTZ / PRIVACY ═══════════ */
const DatenschutzContent = {
  de: () => (
    <>
      <p>gemäß Verordnung (EU) 2016/679 (DSGVO) und dem niederländischen Uitvoeringswet Algemene verordening gegevensbescherming (UAVG)</p>
      <section><h2>1. Verantwortlicher</h2><p>{CO.legal}<br/>{CO.ceo}<br/>{CO.nl}<br/>E-Mail: <a href={`mailto:${CO.email}`}>{CO.email}</a></p><p>Die niederländische Datenschutzbehörde (Autoriteit Persoonsgegevens) ist die zuständige Aufsichtsbehörde.</p></section>
      <section><h2>2. Verarbeitungstätigkeiten</h2>
        <h3>2.1 Kontaktformular</h3><p>Verarbeitete Daten: Name, E-Mail, Telefon, Unternehmen, Nachricht, Zeitstempel. Zweck: Bearbeitung Ihrer Anfrage. Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO. Speicherdauer: 24 Monate.</p>
        <h3>2.2 Terminbuchung</h3><p>Verarbeitete Daten: Name, E-Mail, Datum/Uhrzeit, Thema. Zweck: Organisation des Beratungsgesprächs. Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO. Speicherdauer: 12 Monate.</p>
        <h3>2.3 KI-Chat (NeXifyAI Advisor)</h3><p>Verarbeitete Daten: Chatverlauf, Session-ID. Technologie: OpenAI GPT (Zero Data Retention). Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO. Speicherdauer: 90 Tage.</p>
        <h3>2.4 Analyse</h3><p>Anonymisierte Nutzungsdaten. Keine Cookies für Tracking. Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO.</p>
      </section>
      <section><h2>3. Auftragsverarbeiter</h2><ul><li><strong>Resend, Inc.</strong> (USA): E-Mail-Versand. SCC gemäß Art. 46 DSGVO.</li><li><strong>OpenAI, Inc.</strong> (USA): Chat-Verarbeitung. SCC + Zero Data Retention.</li><li><strong>MongoDB Atlas</strong>: EU-Rechenzentren (Frankfurt).</li></ul></section>
      <section><h2>4. Ihre Rechte</h2><p>Auskunft (Art. 15), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung (Art. 18), Datenübertragbarkeit (Art. 20), Widerspruch (Art. 21).</p><p>Anfragen an: <a href={`mailto:${CO.email}`}>{CO.email}</a>. Antwort innerhalb von 30 Tagen.</p><p>Beschwerderecht bei der Autoriteit Persoonsgegevens, Den Haag.</p></section>
      <section><h2>5. Cookies</h2><p>Nur technisch notwendige Cookies und localStorage. Keine Drittanbieter-Tracking-Cookies.</p></section>
      <section><h2>6. Datensicherheit</h2><p>SSL/TLS-Verschlüsselung, Argon2-Passwort-Hashing, RBAC, regelmäßige Sicherheitsaudits.</p></section>
      <p className="legal-date">Stand: April 2026</p>
    </>
  ),
  nl: () => (
    <>
      <p>conform Verordening (EU) 2016/679 (AVG) en de Uitvoeringswet Algemene verordening gegevensbescherming (UAVG)</p>
      <section><h2>1. Verwerkingsverantwoordelijke</h2><p>{CO.legal}<br/>{CO.ceo}<br/>{CO.nl}<br/>E-mail: <a href={`mailto:${CO.email}`}>{CO.email}</a></p><p>De Autoriteit Persoonsgegevens (AP) is de bevoegde toezichthouder.</p></section>
      <section><h2>2. Verwerkingsactiviteiten</h2>
        <h3>2.1 Contactformulier</h3><p>Verwerkte gegevens: Naam, e-mail, telefoon, bedrijf, bericht, tijdstempel. Doel: Behandeling van uw aanvraag. Rechtsgrondslag: Art. 6 lid 1 sub b AVG. Bewaartermijn: 24 maanden.</p>
        <h3>2.2 Afspraak boeken</h3><p>Verwerkte gegevens: Naam, e-mail, datum/tijd, onderwerp. Doel: Organisatie van het adviesgesprek. Rechtsgrondslag: Art. 6 lid 1 sub b AVG. Bewaartermijn: 12 maanden.</p>
        <h3>2.3 AI-Chat (NeXifyAI Advisor)</h3><p>Verwerkte gegevens: Chatgeschiedenis, sessie-ID. Technologie: OpenAI GPT (Zero Data Retention). Rechtsgrondslag: Art. 6 lid 1 sub f AVG. Bewaartermijn: 90 dagen.</p>
        <h3>2.4 Analyse</h3><p>Geanonimiseerde gebruiksgegevens. Geen tracking-cookies. Rechtsgrondslag: Art. 6 lid 1 sub f AVG.</p>
      </section>
      <section><h2>3. Verwerkers</h2><ul><li><strong>Resend, Inc.</strong> (VS): E-mailverzending. SCC conform Art. 46 AVG.</li><li><strong>OpenAI, Inc.</strong> (VS): Chatverwerking. SCC + Zero Data Retention.</li><li><strong>MongoDB Atlas</strong>: EU-datacenters (Frankfurt).</li></ul></section>
      <section><h2>4. Uw rechten</h2><p>Inzage (Art. 15), Rectificatie (Art. 16), Wissing (Art. 17), Beperking (Art. 18), Overdraagbaarheid (Art. 20), Bezwaar (Art. 21).</p><p>Verzoeken aan: <a href={`mailto:${CO.email}`}>{CO.email}</a>. Reactie binnen 30 dagen.</p><p>Klachtrecht bij de Autoriteit Persoonsgegevens, Den Haag.</p></section>
      <section><h2>5. Cookies</h2><p>Uitsluitend technisch noodzakelijke cookies en localStorage. Geen tracking-cookies van derden.</p></section>
      <section><h2>6. Gegevensbeveiliging</h2><p>SSL/TLS-versleuteling, Argon2-wachtwoordhashing, RBAC, regelmatige beveiligingsaudits.</p></section>
      <p className="legal-date">Status: april 2026</p>
    </>
  ),
  en: () => (
    <>
      <p>pursuant to Regulation (EU) 2016/679 (GDPR) and the Dutch UAVG Implementation Act</p>
      <section><h2>1. Data Controller</h2><p>{CO.legal}<br/>{CO.ceo}<br/>{CO.nl}<br/>Email: <a href={`mailto:${CO.email}`}>{CO.email}</a></p><p>The Dutch Data Protection Authority (Autoriteit Persoonsgegevens) is the competent supervisory authority.</p></section>
      <section><h2>2. Processing Activities</h2>
        <h3>2.1 Contact Form</h3><p>Data processed: Name, email, phone, company, message, timestamp. Purpose: Processing your inquiry. Legal basis: Art. 6(1)(b) GDPR. Retention: 24 months.</p>
        <h3>2.2 Appointment Booking</h3><p>Data processed: Name, email, date/time, topic. Purpose: Organizing the consultation. Legal basis: Art. 6(1)(b) GDPR. Retention: 12 months.</p>
        <h3>2.3 AI Chat (NeXifyAI Advisor)</h3><p>Data processed: Chat transcript, session ID. Technology: OpenAI GPT (Zero Data Retention). Legal basis: Art. 6(1)(f) GDPR. Retention: 90 days.</p>
        <h3>2.4 Analytics</h3><p>Anonymized usage data. No tracking cookies. Legal basis: Art. 6(1)(f) GDPR.</p>
      </section>
      <section><h2>3. Data Processors</h2><ul><li><strong>Resend, Inc.</strong> (USA): Email delivery. SCC per Art. 46 GDPR.</li><li><strong>OpenAI, Inc.</strong> (USA): Chat processing. SCC + Zero Data Retention.</li><li><strong>MongoDB Atlas</strong>: EU data centers (Frankfurt).</li></ul></section>
      <section><h2>4. Your Rights</h2><p>Access (Art. 15), Rectification (Art. 16), Erasure (Art. 17), Restriction (Art. 18), Portability (Art. 20), Objection (Art. 21).</p><p>Requests to: <a href={`mailto:${CO.email}`}>{CO.email}</a>. Response within 30 days.</p><p>Right to lodge a complaint with the Autoriteit Persoonsgegevens, The Hague.</p></section>
      <section><h2>5. Cookies</h2><p>Only technically necessary cookies and localStorage. No third-party tracking cookies.</p></section>
      <section><h2>6. Data Security</h2><p>SSL/TLS encryption, Argon2 password hashing, RBAC, regular security audits.</p></section>
      <p className="legal-date">Last updated: April 2026</p>
    </>
  )
};

/* ═══════════ AGB / TERMS ═══════════ */
const AGBContent = {
  de: () => (
    <>
      <p>der {CO.legal}, eingetragen bei der Kamer van Koophandel unter Nr. {CO.kvk}</p>
      <section><h2>§ 1 Geltungsbereich</h2><p>(1) Diese AGB gelten für alle Geschäftsbeziehungen zwischen {CO.legal} und dem Kunden.</p><p>(2) Niederländisches Recht findet Anwendung, insbesondere Boek 6 BW. Für Verbraucher im DACH-Raum bleiben zwingende Verbraucherschutzvorschriften unberührt (Art. 6 Abs. 2 Rom-I-Verordnung).</p></section>
      <section><h2>§ 2 Vertragsgegenstand</h2><p>Beratungs- und Implementierungsleistungen: KI, Prozessautomation, CRM/ERP-Integration, Softwareentwicklung, Wissenssysteme und IT-Beratung. Leistungsumfang wird individuell festgelegt.</p></section>
      <section><h2>§ 3 Vertragsschluss</h2><p>Angebote sind freibleibend. Vertrag durch schriftliche Auftragsbestätigung. Erstgespräch ist kostenfrei und unverbindlich.</p></section>
      <section><h2>§ 4 Leistungserbringung</h2><p>Leistungen nach Stand der Technik mit Sorgfalt eines ordentlichen Auftragnehmers (Art. 7:401 BW). Termine sind Richttermine (Art. 6:83 BW).</p></section>
      <section><h2>§ 5 Vergütung</h2><p>Preise netto zzgl. BTW. Rechnungen zahlbar innerhalb 14 Tagen. Verzugszinsen gemäß Art. 6:119a BW.</p></section>
      <section><h2>§ 6 Mitwirkungspflichten</h2><p>Kunde stellt Informationen, Zugänge und Ansprechpartner bereit. Verzögerungen durch fehlende Mitwirkung gehen nicht zu Lasten des Anbieters.</p></section>
      <section><h2>§ 7 Datenschutz</h2><p>Verarbeitung gemäß DSGVO und UAVG. AVV bei Auftragsverarbeitung (Art. 28 DSGVO). Gegenseitige Vertraulichkeit.</p></section>
      <section><h2>§ 8 Gewährleistung</h2><p>Leistungen entsprechen Spezifikationen. Mängel unverzüglich melden. Recht zur Nachbesserung.</p></section>
      <section><h2>§ 9 Haftung</h2><p>Beschränkt auf Vorsatz und grobe Fahrlässigkeit. Gesamthaftung begrenzt auf Netto-Auftragswert. Indirekte Schäden ausgeschlossen.</p></section>
      <section><h2>§ 10 Geistiges Eigentum</h2><p>Nicht-exklusives Nutzungsrecht nach Bezahlung. Anbieter behält Recht an generischen Komponenten.</p></section>
      <section><h2>§ 11 Kündigung</h2><p>30 Tage zum Monatsende. Außerordentliche Kündigung aus wichtigem Grund bleibt unberührt.</p></section>
      <section><h2>§ 12 Schlussbestimmungen</h2><p>Niederländisches Recht. Gerichtsstand Limburg (NL). Salvatorische Klausel. Schriftformerfordernis.</p></section>
      <p className="legal-date">Stand: April 2026</p>
    </>
  ),
  nl: () => (
    <>
      <p>van {CO.legal}, ingeschreven bij de Kamer van Koophandel onder nr. {CO.kvk}</p>
      <section><h2>§ 1 Toepassingsgebied</h2><p>(1) Deze voorwaarden gelden voor alle zakelijke relaties tussen {CO.legal} en de opdrachtgever.</p><p>(2) Nederlands recht is van toepassing, in het bijzonder Boek 6 BW. Voor consumenten in de DACH-regio blijven dwingende consumentenbeschermingsregels onverlet.</p></section>
      <section><h2>§ 2 Onderwerp van de overeenkomst</h2><p>Advies- en implementatiediensten: AI, procesautomatisering, CRM/ERP-integratie, softwareontwikkeling, kennissystemen en IT-advies.</p></section>
      <section><h2>§ 3 Totstandkoming overeenkomst</h2><p>Offertes zijn vrijblijvend. Overeenkomst door schriftelijke opdrachtbevestiging. Eerste adviesgesprek is kosteloos en vrijblijvend.</p></section>
      <section><h2>§ 4 Dienstverlening</h2><p>Diensten worden geleverd naar de stand van de techniek met de zorgvuldigheid van een goed opdrachtnemer (Art. 7:401 BW).</p></section>
      <section><h2>§ 5 Vergoeding</h2><p>Prijzen exclusief BTW. Facturen betaalbaar binnen 14 dagen. Wettelijke handelsrente bij verzuim (Art. 6:119a BW).</p></section>
      <section><h2>§ 6 Medewerkingsverplichtingen</h2><p>Opdrachtgever stelt benodigde informatie, toegang en contactpersonen beschikbaar.</p></section>
      <section><h2>§ 7 Privacy</h2><p>Verwerking conform AVG en UAVG. Verwerkersovereenkomst bij verwerking (Art. 28 AVG). Wederzijdse vertrouwelijkheid.</p></section>
      <section><h2>§ 8 Garantie</h2><p>Diensten voldoen aan specificaties. Gebreken onverwijld melden. Recht op herstel.</p></section>
      <section><h2>§ 9 Aansprakelijkheid</h2><p>Beperkt tot opzet en grove schuld. Totale aansprakelijkheid beperkt tot netto opdrachtwaarde.</p></section>
      <section><h2>§ 10 Intellectueel eigendom</h2><p>Niet-exclusief gebruiksrecht na betaling. Opdrachtnemer behoudt recht op generieke componenten.</p></section>
      <section><h2>§ 11 Opzegging</h2><p>30 dagen opzegtermijn per maandeinde. Buitengewone opzegging om gewichtige redenen blijft mogelijk.</p></section>
      <section><h2>§ 12 Slotbepalingen</h2><p>Nederlands recht. Bevoegde rechter: Limburg (NL). Partiële nietigheid. Schriftelijkheidsvereiste.</p></section>
      <p className="legal-date">Status: april 2026</p>
    </>
  ),
  en: () => (
    <>
      <p>of {CO.legal}, registered with the Chamber of Commerce under no. {CO.kvk}</p>
      <section><h2>§ 1 Scope</h2><p>(1) These terms apply to all business relationships between {CO.legal} and the client.</p><p>(2) Dutch law applies, in particular Book 6 of the Dutch Civil Code (BW). Mandatory consumer protection rules for DACH consumers remain unaffected.</p></section>
      <section><h2>§ 2 Subject Matter</h2><p>Consulting and implementation services: AI, process automation, CRM/ERP integration, software development, knowledge systems and IT consulting.</p></section>
      <section><h2>§ 3 Contract Formation</h2><p>Offers are non-binding. Contract through written order confirmation. Initial consultation is free and non-binding.</p></section>
      <section><h2>§ 4 Service Delivery</h2><p>Services delivered according to state of the art with the care of a proper contractor (Art. 7:401 BW).</p></section>
      <section><h2>§ 5 Compensation</h2><p>Prices net plus VAT (BTW). Invoices payable within 14 days. Statutory commercial interest on late payment (Art. 6:119a BW).</p></section>
      <section><h2>§ 6 Client Obligations</h2><p>Client provides required information, access and contact persons in a timely manner.</p></section>
      <section><h2>§ 7 Data Protection</h2><p>Processing in accordance with GDPR and UAVG. Data processing agreement for processing (Art. 28 GDPR). Mutual confidentiality.</p></section>
      <section><h2>§ 8 Warranty</h2><p>Services comply with specifications. Defects to be reported immediately. Right to remedy.</p></section>
      <section><h2>§ 9 Liability</h2><p>Limited to intent and gross negligence. Total liability limited to net order value.</p></section>
      <section><h2>§ 10 Intellectual Property</h2><p>Non-exclusive usage rights upon payment. Provider retains rights to generic components.</p></section>
      <section><h2>§ 11 Termination</h2><p>30 days notice to end of month. Extraordinary termination for cause remains unaffected.</p></section>
      <section><h2>§ 12 Final Provisions</h2><p>Dutch law applies. Jurisdiction: Limburg (NL). Severability clause. Written form requirement.</p></section>
      <p className="legal-date">Last updated: April 2026</p>
    </>
  )
};

/* ═══════════ KI-HINWEISE / AI TRANSPARENCY ═══════════ */
const TITLES = {
  impressum: { de: 'Impressum', nl: 'Impressum', en: 'Imprint' },
  datenschutz: { de: 'Datenschutzerklärung', nl: 'Privacybeleid', en: 'Privacy Policy' },
  agb: { de: 'Allgemeine Geschäftsbedingungen', nl: 'Algemene Voorwaarden', en: 'Terms and Conditions' },
  ki: { de: 'KI-Hinweise & Transparenz', nl: 'AI-Informatie & Transparantie', en: 'AI Transparency Notice' }
};

const KIContent = {
  de: () => (
    <>
      <p>gemäß Verordnung (EU) 2024/1689 (EU AI Act)</p>
      <section><h2>1. Einsatz von KI-Systemen</h2><p>{CO.legal} setzt KI-gestützte Systeme ein. Diese Seite informiert Sie gemäß Art. 52 AI Act.</p></section>
      <section><h2>2. KI auf dieser Website</h2>
        <h3>2.1 NeXifyAI Advisor (Live-Chat)</h3><p>KI-Dialogsystem (OpenAI GPT-4o-mini). Verarbeitet Textnachrichten kontextbezogen für Erstberatung und Terminbuchung.</p>
        <p><strong>Grenzen:</strong> Keine rechtsverbindlichen Zusagen, keine Preisgarantien, kann halluzinieren. Ersetzt keine Fachberatung.</p>
        <p><strong>Risikoklasse:</strong> Minimales Risiko (Art. 6 AI Act).</p>
        <h3>2.2 Nutzungsanalyse</h3><p>Anonymisierte Nutzungsdaten. Keine KI-basierte Profilierung.</p>
      </section>
      <section><h2>3. Transparenz und Kontrolle</h2><ul><li>Alle KI-Interaktionen sind gekennzeichnet (Art. 52 AI Act).</li><li>Human-in-the-Loop bei kritischen Entscheidungen.</li><li>Recht auf menschliche Bearbeitung.</li><li>Audit-Trail (Art. 12 AI Act).</li><li>Keine biometrische Identifikation, kein Social Scoring (Art. 5 AI Act).</li></ul></section>
      <section><h2>4. Datenverarbeitung</h2><p>Keine Verwendung Ihrer Daten für KI-Training. Isolierte Umgebungen. Zero-Data-Retention bei Drittanbietern.</p></section>
      <section><h2>5. Kontakt</h2><p>{CO.legal}<br/>E-Mail: <a href={`mailto:${CO.email}`}>{CO.email}</a><br/>Telefon: {CO.phone}</p></section>
      <p className="legal-date">Stand: April 2026</p>
    </>
  ),
  nl: () => (
    <>
      <p>conform Verordening (EU) 2024/1689 (EU AI Act)</p>
      <section><h2>1. Gebruik van AI-systemen</h2><p>{CO.legal} maakt gebruik van AI-systemen. Deze pagina informeert u conform Art. 52 AI Act.</p></section>
      <section><h2>2. AI op deze website</h2>
        <h3>2.1 NeXifyAI Advisor (Live-Chat)</h3><p>AI-dialoogsysteem (OpenAI GPT-4o-mini). Verwerkt tekstberichten contextueel voor eerste advies en afspraken.</p>
        <p><strong>Beperkingen:</strong> Geen juridisch bindende toezeggingen, geen prijsgaranties, kan hallucineren. Vervangt geen vakadvies.</p>
        <p><strong>Risicoklasse:</strong> Minimaal risico (Art. 6 AI Act).</p>
        <h3>2.2 Gebruiksanalyse</h3><p>Geanonimiseerde gebruiksgegevens. Geen AI-gebaseerde profilering.</p>
      </section>
      <section><h2>3. Transparantie en controle</h2><ul><li>Alle AI-interacties zijn gemarkeerd (Art. 52 AI Act).</li><li>Human-in-the-loop bij kritieke beslissingen.</li><li>Recht op menselijke verwerking.</li><li>Audittrail (Art. 12 AI Act).</li><li>Geen biometrische identificatie, geen social scoring (Art. 5 AI Act).</li></ul></section>
      <section><h2>4. Gegevensverwerking</h2><p>Uw gegevens worden niet gebruikt voor AI-training. Geïsoleerde omgevingen. Zero-Data-Retention bij derde partijen.</p></section>
      <section><h2>5. Contact</h2><p>{CO.legal}<br/>E-mail: <a href={`mailto:${CO.email}`}>{CO.email}</a><br/>Telefoon: {CO.phone}</p></section>
      <p className="legal-date">Status: april 2026</p>
    </>
  ),
  en: () => (
    <>
      <p>pursuant to Regulation (EU) 2024/1689 (EU AI Act)</p>
      <section><h2>1. Use of AI Systems</h2><p>{CO.legal} employs AI-powered systems. This page informs you pursuant to Art. 52 AI Act.</p></section>
      <section><h2>2. AI on this Website</h2>
        <h3>2.1 NeXifyAI Advisor (Live Chat)</h3><p>AI dialogue system (OpenAI GPT-4o-mini). Processes text messages contextually for initial consultation and appointment booking.</p>
        <p><strong>Limitations:</strong> No legally binding commitments, no price guarantees, may hallucinate. Does not replace professional advice.</p>
        <p><strong>Risk class:</strong> Minimal risk (Art. 6 AI Act).</p>
        <h3>2.2 Usage Analytics</h3><p>Anonymized usage data. No AI-based profiling.</p>
      </section>
      <section><h2>3. Transparency and Control</h2><ul><li>All AI interactions are labeled (Art. 52 AI Act).</li><li>Human-in-the-loop for critical decisions.</li><li>Right to human processing.</li><li>Audit trail (Art. 12 AI Act).</li><li>No biometric identification, no social scoring (Art. 5 AI Act).</li></ul></section>
      <section><h2>4. Data Processing</h2><p>Your data is not used for AI training. Isolated environments. Zero-Data-Retention with third parties.</p></section>
      <section><h2>5. Contact</h2><p>{CO.legal}<br/>Email: <a href={`mailto:${CO.email}`}>{CO.email}</a><br/>Phone: {CO.phone}</p></section>
      <p className="legal-date">Last updated: April 2026</p>
    </>
  )
};

const CONTENT_MAP = { impressum: ImpressumContent, datenschutz: DatenschutzContent, agb: AGBContent, ki: KIContent };

/* Slug to page mapping */
const SLUG_MAP = {
  impressum: 'impressum', imprint: 'impressum',
  datenschutz: 'datenschutz', privacy: 'datenschutz', privacybeleid: 'datenschutz',
  agb: 'agb', terms: 'agb', voorwaarden: 'agb',
  'ki-hinweise': 'ki', 'ai-transparency': 'ki', 'ai-informatie': 'ki'
};

export default function LegalPage() {
  const { lang: urlLang, page: slug } = useParams();
  const { lang } = useLanguage();

  if (!SUPPORTED.includes(urlLang)) {
    return <Navigate to={`/de/${slug || ''}`} replace />;
  }

  const pageKey = SLUG_MAP[slug];
  if (!pageKey) return <Navigate to={`/${lang}`} replace />;

  const content = CONTENT_MAP[pageKey];
  const Render = content[lang] || content.en;
  const title = TITLES[pageKey][lang] || TITLES[pageKey].en;

  return <LegalWrap title={title}><Render /></LegalWrap>;
}
