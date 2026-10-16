# Ancore del registro delle decisioni (produzione)

L'ancora è la posizione e l'hash dell'ultima riga del registro delle decisioni in un dato momento. Conservata fuori dal database, permette all'auditor di verificare che nessuna riga sia stata alterata o tolta dopo quel momento:
`neartech.registro.verifica_catena(conn, ancora=(posizione, hash))` restituisce `None` se la catena è integra.

Ogni riga si aggiunge, non si modifica. Dopo un gruppo di scritture rilevanti in produzione se ne registra una nuova.

| Data | Posizione | Hash | Dopo |
|---|---|---|---|
| 2026-10-16 | 10 | `43e761b5cba1a8deaf9ede4bdad314e238fa762283720a989ed98b978ce8ac3e` | Bootstrap dell'amministratore tecnico, copia del testo di Società Dolce in `org_societa_dolce`, ruolo di revisore, parametri comuni (soglia 0,9; parziali come errori; confidenza 0,95), campione delle 61 fusioni (`86199f1e-ca89-42d3-af9e-b5837b3675c1`) |
