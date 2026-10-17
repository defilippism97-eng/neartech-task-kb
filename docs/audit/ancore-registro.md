# Ancore del registro delle decisioni (produzione)

L'ancora è la posizione e l'hash dell'ultima riga del registro delle decisioni in un dato momento. Conservata fuori dal database, permette all'auditor di verificare che nessuna riga sia stata alterata o tolta dopo quel momento:
`neartech.registro.verifica_catena(conn, ancora=(posizione, hash))` restituisce `None` se la catena è integra.

Ogni riga si aggiunge, non si modifica. Dopo un gruppo di scritture rilevanti in produzione se ne registra una nuova.

| Data | Posizione | Hash | Dopo |
|---|---|---|---|
| 2026-10-16 | 10 | `43e761b5cba1a8deaf9ede4bdad314e238fa762283720a989ed98b978ce8ac3e` | Bootstrap dell'amministratore tecnico, copia del testo di Società Dolce in `org_societa_dolce`, ruolo di revisore, parametri comuni (soglia 0,9; parziali come errori; confidenza 0,95), campione delle 61 fusioni (`86199f1e-ca89-42d3-af9e-b5837b3675c1`) |
| 2026-10-16 | 14 | `d71bd40912908d63ccd59816b8ee52c448a43a4bf75abc4385e963ff0e99eeee` | 61 giudizi registrati e misura ufficiale (75,4%, sotto soglia); campione casuale delle 'diversa' (`c50ba757-d86e-4979-98ed-15c93d4cd6a3`); migrazione 0021; separazione delle 3 fusioni errate (elementi 13, 26, 39): task attivi da 295 a 298 |
| 2026-10-16 | 22 | `6723600d65127baa8c276ca3f9a8f56ba3bbe1c3f0fb1330d11339bbe2463074` | Separazione delle 8 fusioni parziali approvate (elementi 5, 9, 32, 59, 33, 41, 43, 55): task attivi da 298 a 306 |
| 2026-10-17 | 23 | `277d2305709cacb51ac1000b59717c3bde91daf57dd87a28c8358968c50f2d59` | Migrazioni 0023 e org 0005; testo di Società Dolce tolto da `public` (504 occorrenze, 36 ruoli, 36 documenti con nome neutro); migrazione 0024 (vincoli convalidati su tutte le righe) |
| 2026-10-17 | 25 | `42507d4dc60f57bef643d749d9ebcefaa7a7a915f88c8fbebc9b75375fdb5b15` | Migrazioni 0026–0031 e org 0007–0008; 16 note dei giudizi spostate nello spazio; parametro comune `quota_revisione_abbinamenti` = 0,20 proposto e approvato (registro di metodo, sezione 17) |
| 2026-10-17 | 37 | `ebe855847ba7b8b2ad6f1043f5ca5fd8cb7300d2d0a780d5da251736e09517c9` | Migrazioni 0032–0034 e org 0009; importazione delle etichette silver v2 come giudizi di modello (rubrica `bozza-3` in bozza): 2.094 giudizi N e 778 D in sei campagne, completati con la seconda esecuzione (41 giudizi identici di task diversi) |
| 2026-10-17 | 39 | `223c8cf0a0fc729f23d4b96607498e653e9b88116b1fe8a47ccda0a3629c315d` | Rubrica `bozza-3` approvata come corrente (provvisoria) e profilo di pesi comune `neartech-comune-v1` approvato e attivo (valori dell'esempio del piano) |
| 2026-10-17 | 42 | `8a66420e3697464112461d214116a97db6cee61608d6a82a4a37100c64460e1c` | Copertura di riserva dei 306 task (Haiku 5.5: 306 chiamate, 150.689 token in ingresso e 248.140 in uscita); snapshot di riserva `fe46a606-4c20-415a-8da9-59f64bf3f59a` (riserva-v2-banda-0.5, emivita 180 giorni) proposto e pubblicato; primo calcolo di N e D per Società Dolce (504 risultati, seme 20261017, 2.000 estrazioni) |
| 2026-10-17 | 44 | `7763d92864438958d523fd1435d8a51809ae7a75a442f7d6f2f5acc4f13d0215` | Migrazione 0036 (restituzione); parametro comune `soglia_stabilita_quadrante` = 0,8 proposto e approvato (registro di metodo, sezione 25) |
