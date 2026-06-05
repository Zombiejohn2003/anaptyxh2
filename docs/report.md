# Αναφορά υλοποίησης εφαρμογής Sensor Dashboard

## 1. Περιβάλλον υλοποίησης

Η εφαρμογή υλοποιήθηκε ως διαδικτυακό σύστημα δύο επιπέδων, με ξεχωριστό backend και frontend:

- **Backend:** Flask REST API σε Python.
- **Frontend:** React εφαρμογή με Vite.
- **Βάση δεδομένων:** PostgreSQL, δηλαδή σχεσιακή βάση διαφορετική από SQLite όπως ζητείται στην εκφώνηση.
- **Επικοινωνία frontend-backend:** HTTP requests από το React προς το Flask API με χρήση JSON.
- **Authentication:** JSON Web Tokens (JWT).
- **Role based access control:** δύο ρόλοι χρηστών, `user` και `admin`.

### 1.1 Backend βιβλιοθήκες

Οι βιβλιοθήκες του backend βρίσκονται στο αρχείο `backend/requirements.txt`:

| Βιβλιοθήκη | Χρήση |
| --- | --- |
| `Flask` | Δημιουργία του REST API και των routes. |
| `Flask-Cors` | Επιτρέπει στο React frontend να επικοινωνεί με το Flask API από διαφορετικό port. |
| `Flask-JWT-Extended` | Δημιουργία και έλεγχος JWT tokens για authentication. |
| `Flask-SQLAlchemy` | ORM για σύνδεση των Python models με τους πίνακες της PostgreSQL. |
| `psycopg2-binary` | PostgreSQL driver για τη σύνδεση Python/PostgreSQL. |
| `python-dotenv` | Φόρτωση μεταβλητών περιβάλλοντος από `.env`, όπου χρειάζεται. |

### 1.2 Frontend βιβλιοθήκες

Οι βασικές βιβλιοθήκες του frontend βρίσκονται στο `frontend/package.json` και εγκαθίστανται με `npm install`:

| Βιβλιοθήκη | Χρήση |
| --- | --- |
| `react` / `react-dom` | Υλοποίηση της διεπαφής χρήστη. |
| `vite` | Development server και production build για το React project. |
| `axios` | HTTP client για κλήσεις προς το Flask API. |
| `recharts` | Δημιουργία γραφημάτων dashboard και χρονοσειρών αισθητήρων. |
| `lucide-react` | Icons για κουμπιά και βασικά στοιχεία UI. |
| `eslint` | Έλεγχος ποιότητας/σύνταξης του frontend κώδικα. |

### 1.3 Βάση δεδομένων

Η βάση είναι PostgreSQL και μπορεί να εκκινηθεί με Docker Compose. Το αρχείο `docker-compose.yml` δημιουργεί service `db` με:

- Database: `sensor_dashboard`
- User: `sensor_user`
- Password: `sensor_password`
- Port: `5432`

Το αρχείο `database/schema_seed.sql` περιέχει τη δομή των πινάκων και αρχικά δεδομένα. Εναλλακτικά, το script `backend/seed.py` δημιουργεί και γεμίζει τη βάση μέσω SQLAlchemy.

Οι βασικοί πίνακες είναι:

- `users`: λογαριασμοί χρηστών και ρόλοι.
- `sensors`: μεταδεδομένα αισθητήρων.
- `measurement_categories`: κατηγορίες μετρήσεων, π.χ. temperature και humidity.
- `sensor_categories`: ενδιάμεσος πίνακας many-to-many, επειδή ένας αισθητήρας μπορεί να έχει μία ή περισσότερες κατηγορίες.
- `measurements`: ιστορικές μετρήσεις αισθητήρων.

## 2. Βήματα εγκατάστασης και εκτέλεσης

### 2.1 Προαπαιτούμενα

Στον υπολογιστή πρέπει να υπάρχουν εγκατεστημένα:

1. **Python 3**
2. **Node.js και npm**
3. **Docker Desktop** ή άλλη εγκατάσταση PostgreSQL
4. **Git** προαιρετικά, αν γίνει clone από repository

### 2.2 Εκκίνηση PostgreSQL

Από τον κεντρικό φάκελο του project εκτελούμε:

```bash
docker compose up -d db
```

Η εντολή ξεκινά container PostgreSQL στο port `5432`.

Αν δεν χρησιμοποιηθεί Docker, πρέπει να δημιουργηθεί χειροκίνητα PostgreSQL βάση με τα στοιχεία σύνδεσης που υπάρχουν στο `.env.example`.

### 2.3 Ρύθμιση μεταβλητών περιβάλλοντος

Το project περιλαμβάνει αρχείο `.env.example` με ενδεικτικές τιμές:

```env
DATABASE_URL=postgresql+psycopg2://sensor_user:sensor_password@localhost:5432/sensor_dashboard
JWT_SECRET_KEY=replace-with-a-long-random-secret
INGEST_API_KEY=dev-ingest-token
FRONTEND_ORIGIN=http://localhost:5173
VITE_API_URL=http://localhost:5000/api
```

Για τοπική εκτέλεση μπορεί να αντιγραφεί σε `.env` ή να οριστούν οι ίδιες τιμές στο terminal.

### 2.4 Εγκατάσταση και εκτέλεση backend

Από τον κεντρικό φάκελο του project:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python run.py
```

Σε Windows CMD οι αντίστοιχες εντολές είναι:

```cmd
cd backend
py -m venv .venv
.venv\Scriptsctivate
pip install -r requirements.txt
py seed.py
py run.py
```

Το backend τρέχει στο:

```text
http://localhost:5000
```

Έλεγχος ότι λειτουργεί:

```text
http://localhost:5000/health
```

Αν όλα είναι σωστά, επιστρέφει:

```json
{"status":"ok"}
```

### 2.5 Εγκατάσταση και εκτέλεση frontend

Σε δεύτερο terminal:

```bash
cd frontend
npm install
npm run dev
```

Το frontend ανοίγει συνήθως στο:

```text
http://localhost:5173
```

### 2.6 Demo λογαριασμοί

Μετά το `seed.py` υπάρχουν οι εξής λογαριασμοί:

| Ρόλος | Username | Password |
| --- | --- | --- |
| Διαχειριστής | `admin` | `admin123` |
| Απλός χρήστης | `user` | `user123` |

Ο απλός χρήστης έχει μόνο δικαιώματα ανάγνωσης. Ο διαχειριστής έχει πλήρη δικαιώματα CRUD για αισθητήρες και χρήστες.

## 3. Σύντομη περιγραφή διαδικασίας υλοποίησης

Αρχικά σχεδιάστηκε το σχήμα της βάσης δεδομένων με βάση τις απαιτήσεις της εκφώνησης. Δημιουργήθηκαν πίνακες για χρήστες, αισθητήρες, κατηγορίες μετρήσεων και ιστορικές μετρήσεις. Οι κατηγορίες temperature και humidity αποθηκεύονται ως ξεχωριστές οντότητες στη βάση, ώστε η φόρμα δημιουργίας/επεξεργασίας αισθητήρα να τις φορτώνει δυναμικά.

Στη συνέχεια υλοποιήθηκε το Flask backend. Δημιουργήθηκαν SQLAlchemy models για τους πίνακες και REST endpoints για login, dashboard δεδομένα, αισθητήρες, χρήστες και μετρήσεις. Το authentication γίνεται με JWT token. Όταν ο χρήστης κάνει login, το backend ελέγχει username/password και επιστρέφει token. Το token χρησιμοποιείται στις επόμενες κλήσεις API.

Για τον έλεγχο πρόσβασης δημιουργήθηκε μηχανισμός role based access control. Οι απλοί χρήστες μπορούν να δουν dashboard, πίνακα αισθητήρων και λεπτομέρειες αισθητήρα. Οι διαχειριστές μπορούν επιπλέον να δημιουργούν, να επεξεργάζονται και να διαγράφουν αισθητήρες και χρήστες. Τα admin endpoints προστατεύονται στο backend, άρα ακόμη και αν κάποιος κρύψει/αλλάξει το frontend, δεν μπορεί να εκτελέσει admin ενέργειες χωρίς admin token.

Έπειτα υλοποιήθηκε το React frontend. Η αρχική οθόνη είναι η φόρμα σύνδεσης. Μετά από επιτυχημένο login, το token αποθηκεύεται στο `localStorage` και η εφαρμογή εμφανίζει το dashboard. Το dashboard περιλαμβάνει κάρτες σύνοψης, γραφήματα, πίνακα αισθητήρων και, μόνο για διαχειριστές, πίνακα χρηστών. Οι φόρμες δημιουργίας/επεξεργασίας εμφανίζονται μόνο όταν ο χρήστης έχει ρόλο admin.

Για την οπτικοποίηση χρησιμοποιήθηκε η βιβλιοθήκη Recharts. Στο κεντρικό dashboard εμφανίζονται aggregate γραφήματα, ενώ στη σελίδα λεπτομερειών αισθητήρα εμφανίζεται γράφημα χρονοσειράς. Ο χρήστης μπορεί να αλλάξει την ανάλυση των δεδομένων σε hour, day ή month. Η ομαδοποίηση γίνεται στο backend με PostgreSQL `date_trunc`, ώστε τα δεδομένα να επιστρέφονται ήδη συγκεντρωτικά στο frontend.

Τέλος, υλοποιήθηκε προαιρετικό endpoint για αυτοματοποιημένη εισαγωγή μετρήσεων:

```text
POST /api/measurements/ingest
```

Το endpoint προστατεύεται με header `X-API-Key`. Ελέγχει ότι ο αισθητήρας υπάρχει και ότι η κατηγορία μέτρησης ανήκει στον συγκεκριμένο αισθητήρα πριν αποθηκεύσει τη νέα μέτρηση.

## 4. Έλεγχος λειτουργίας

Για βασικό έλεγχο εκτελέστηκαν:

```bash
npm run lint
npm run build
python3 -m compileall backend
```

Επίσης έγινε έλεγχος ότι το Flask app φορτώνει σωστά και ότι το `/health` endpoint επιστρέφει `{"status":"ok"}`.

## 5. Παραδοτέα αρχεία

Τα βασικά αρχεία του project είναι:

- `backend/`: Flask API.
- `frontend/`: React εφαρμογή.
- `database/schema_seed.sql`: SQL dump με schema και seed data.
- `docker-compose.yml`: PostgreSQL service.
- `.env.example`: ενδεικτικές μεταβλητές περιβάλλοντος.
- `docs/report.md`: η παρούσα αναφορά, η οποία μπορεί να μετατραπεί σε PDF.
