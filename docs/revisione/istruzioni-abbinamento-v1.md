# Istruzioni di revisione: abbinamento al dataset consolidato (versione `istruzioni-abbinamento-v1`)

**Stato: bozza, da approvare** dal responsabile del progetto. Una modifica richiede una versione nuova. Il codice della versione (`istruzioni-abbinamento-v1`) va indicato in ogni campione e in ogni giudizio.

## Cosa si rivede

Coppie formate da un'attività estratta dai documenti dell'organizzazione (il **candidato**) e dal task del dataset consolidato che il sistema propone come corrispondente: il più vicino per significato. Per ogni coppia vedete il titolo del candidato, il titolo del task proposto e la proposta del sistema ("stesso task"). Non vedete la distanza né gli altri vicini: la revisione è cieca rispetto al calcolo.

Se il candidato è approvato, l'organizzazione eredita la classificazione del task del dataset (N e D). Un abbinamento sbagliato porta all'organizzazione la classificazione di un altro compito.

## Definizione

Il candidato **corrisponde** al task proposto quando descrivono lo stesso compito di lavoro: stesso risultato e stesso oggetto, anche con parole diverse. È la stessa definizione delle fusioni (`istruzioni-fusioni-v1`), con le distinzioni emerse dalla revisione delle 61 fusioni (registro di metodo, sezione 11): non corrispondono un compito esecutivo e un compito di responsabilità sullo stesso oggetto, né un compito e uno più ampio che lo comprende.

## Esiti

| Esito | Quando |
|---|---|
| `corretto` | Il candidato è lo stesso task del dataset. |
| `parziale` | I due si sovrappongono molto ma non coincidono: per esempio uno è più ampio, o la differenza dipende dal contesto dell'organizzazione. Scrivete il motivo nella nota. |
| `errato` | Il candidato è un compito diverso. Scrivete nella nota, se lo conoscete, il task del dataset a cui corrisponde, oppure che è un task nuovo. |

Come conta "parziale" nella precisione lo fissa il parametro `regola_parziali` (oggi: conta come errore).

## Dopo il campione

La misura di precisione sul campione accompagna la decisione sul lotto. Chi decide il lotto lo approva in blocco e indica le proposte da rifiutare: quelle giudicate `errato` o `parziale` nel campione e le altre che ritiene sbagliate guardando la coda di revisione, che mette in testa le proposte più ambigue. Una proposta rifiutata diventa un task nuovo del dataset.

## Regole pratiche

- Giudicate la coppia così come è scritta.
- Un dubbio non risolto è un `parziale` con nota, non un `corretto`.
- Se cambiate idea, registrate un nuovo giudizio: il precedente resta nello storico e conta l'ultimo.
- Se due revisori danno esiti diversi, il calcolo della metrica si ferma finché non concordate.
