# Ekranų CRM Sistema

Ekranų reklamos valdymo sistema, skirta ekranų teikėjams ir jų ekranų administravimui.

## Funkcionalumas

### Ekranų Teikėjai
- Teikėjų registracija ir kontaktinės informacijos valdymas
- Teikėjų sąrašas ir detalus peržiūrėjimas

### Ekranai
Kiekvienas ekranas turi šią informaciją:
- **Pagrindinė informacija**: pavadinimas, nuotrauka, pozicijos aprašymas, komentaras
- **Ekrano tipas**: horizontalus/vertikalus
- **Turinio tipas**: video (judantis vaizdas) / statinis (nejudantis)
- **Parametrai**: ilgis, plotis (metrais)
- **Pikseliai**: ekrano raiška (pikseliais)
- **Lokacija**: 
  - GPS koordinatės (platuma, ilguma)
  - Miestas
  - Adresas
  - Pusė (D-dešinė, K-kairė)

### Įkainis
Kiekvienas ekranas turi valandinius įkainius:
- Kaina už tūkstantį kontaktų kiekvienai valandai (0-23)
- Kontaktų kiekis kiekvienai valandai

## Technologijos

- **Backend**: Flask (Python)
- **Duomenų bazė**: SQLite su SQLAlchemy ORM
- **Frontend**: Bootstrap 5, HTML templates
- **Migracijos**: Flask-Migrate

## Diegimas

1. Sukurkite virtualią aplinką:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# arba
venv\Scripts\activate     # Windows
```

2. Įdiekite priklausomybes:
```bash
pip install -r requirements.txt
```

3. Paleiskite aplikaciją:
```bash
python run.py
```

4. Atidarykite naršyklėje: http://localhost:5003

## Duomenų bazės struktūra

### ScreenProvider (Teikėjai)
- id, name, email, phone, contact_person, created_at

### Screen (Ekranai)  
- id, provider_id, name, image_path, position_description, comment
- screen_type, content_type, width, height, pixel_width, pixel_height
- gps_latitude, gps_longitude, city, address, side, created_at

### ScreenPricing (Įkainis)
- id, screen_id, hour (0-23), price_per_thousand_contacts, contact_count

## Naudojimas

1. **Pridėkite teikėją** - užregistruokite ekranų teikėją su kontaktine informacija
2. **Pridėkite ekranus** - kiekvienam teikėjui pridėkite ekranus su visais parametrais
3. **Nustatykite įkainius** - kiekvienam ekranui sukonfigūruokite valandinius įkainius
4. **Peržiūrėkite informaciją** - naudokitės patogia sąsaja ekranų ir teikėjų valdymui