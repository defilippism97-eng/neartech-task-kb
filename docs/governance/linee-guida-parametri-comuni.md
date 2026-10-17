# Linee guida per il comitato guida: i parametri comuni

Versione 1, 2026-10-17. Decisione del responsabile del progetto: metodologia, sezione 10 (decisione b).

## A cosa servono

L'amministratore tecnico imposta i parametri NEARTECH comuni a tutte le organizzazioni. Il comitato guida di ogni organizzazione li vede, con valore, versione e descrizione, e per ciascuno può:

- **adottarlo**, cioè confermare che il valore comune va bene per l'organizzazione;
- **chiedere una ricalibrazione** all'amministratore tecnico, con una motivazione obbligatoria.

Entrambe sono decisioni registrate. La motivazione sta nello spazio dell'organizzazione (ADR 0004) ed entra nel suo report di audit. Se l'amministratore approva una versione nuova, il comitato la deve esaminare di nuovo: l'adozione vale per una versione.

In alternativa il comitato può approvare un valore proprio dell'organizzazione, che sostituisce quello comune (`parametro_proprio`).

Il valore comune si applica anche prima dell'adozione. Ogni risultato riporta la versione del parametro usata, e il report di audit dice se l'organizzazione l'aveva adottata.

## Stati che il comitato vede

| Stato | Significato |
|---|---|
| `da_esaminare` | Il comitato non si è ancora espresso sulla versione vigente. |
| `adottato` | Il comitato ha adottato la versione vigente. |
| `ricalibrazione_richiesta` | Il comitato ha chiesto all'amministratore di rivedere il valore. |
| `parametro_proprio` | L'organizzazione ha deciso un valore proprio. |

## I parametri e il loro effetto sul processo

I tre parametri riguardano la **misura di precisione**: la quota di proposte del modello (per esempio fusioni di task o abbinamenti al dataset consolidato) che i revisori giudicano corrette in un campione. La misura dice se le proposte del modello sono affidabili abbastanza da essere usate senza rivederle tutte.

### `soglia_precisione_abbinamento` (valore comune 0,9)

Precisione minima perché le proposte del modello siano considerate affidabili. Sotto soglia la misura registra `sotto_soglia`: prima di usare le proposte, vanno riviste o il prompt va ricalibrato (come per le 61 fusioni, sezione 11 della metodologia).
- **Più alta:** più proposte respinte e più revisione umana, meno errori nel dataset.
- **Più bassa:** meno lavoro di revisione, più errori che arrivano alle classificazioni dei task, e quindi ai valori di N e D.

Se la soglia cade dentro l'intervallo di confidenza, l'esito non è conclusivo: il report lo dice e serve un campione più grande.

### `regola_parziali` (valore comune: `errore`)

Come contare le proposte che i revisori giudicano parzialmente corrette.
- `errore`: contano come errori. È la regola più prudente.
- `corretto`: contano come corrette. La precisione sale.
- `escluso`: non entrano nel calcolo. Il campione utile si riduce.

Sulla prima misura (61 fusioni) la regola cambia l'esito: 75,4% con i parziali come errori.

### `livello_confidenza` (valore comune 0,95)

Livello dell'intervallo di Wilson attorno alla precisione misurata.
- **Più alto:** intervallo più largo; serve un campione più grande per un esito conclusivo.
- **Più basso:** intervallo più stretto, con più rischio di un esito dovuto al caso.

## Come leggere una richiesta di ricalibrazione

Una buona motivazione dice che cosa nella situazione dell'organizzazione rende il valore comune inadatto: per esempio, un'organizzazione piccola con campioni ridotti, o un settore in cui un errore di classificazione pesa di più. L'amministratore risponde con una nuova versione del parametro comune oppure lasciando il valore com'è. In entrambi i casi la sua decisione è un atto registrato con la motivazione.

Nell'elenco delle richieste, una richiesta **superata** riguarda una versione comune che non è più vigente: l'amministratore ha già approvato una versione nuova o ritirato quella. Il comitato vede la versione vigente e può adottarla o chiedere di nuovo una ricalibrazione.

## Contrappesi

Chi propone un parametro dell'organizzazione può anche approvarlo; l'atto lo segna (`stesso_proponente`). I revisori, che giudicano le classificazioni risultanti, possono segnalare al comitato i bias che derivano dalle sue decisioni; nel comitato può sedere il rappresentante dei lavoratori.

## Parametri futuri

La quota di revisione a campione dei task nuovi (fase 3) sarà un parametro comune con le stesse regole; queste linee guida si aggiorneranno con il suo effetto.
