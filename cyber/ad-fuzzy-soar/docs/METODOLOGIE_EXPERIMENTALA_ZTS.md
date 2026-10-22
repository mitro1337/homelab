# Metodologie Experimentală — Evaluarea Sistemului Fuzzy de Risc în Active Directory

**Lucrare elaborată pentru:** Sesiunea de Comunicări Științifice Studențești — *Zilele Tehnicii Studențești (ZTS)* / Lucrare de Licență  
**Autor:** Moană Ștefănuț-Cornel  
**Domeniu:** Informatică / Securitate Cibernetică și Sisteme Suport de Decizie  
**Cadru aplicativ:** Infrastructură hibridă Active Directory (Windows Server 2022, Windows 10/11, Linux SSSD/Kerberos, Wazuh SIEM 4.8, Suricata NIDS)

---

## 1. Introducere și Formularea Problemei

Evaluarea securității cibernetice în mediile Active Directory (AD) se confruntă cu o provocare structurală majoră: **ambiguitatea contextuală a indicatorilor de compromitere**. În rețelele enterprise, volumul de evenimente de autentificare (Kerberos, NTLM) și acces la obiecte este masiv, iar frontiera dintre activitatea legitimă a utilizatorilor privilegiați și acțiunile atacatorilor (precum *Pass-the-Hash*, *Kerberoasting*, *Token Manipulation* sau *DCSync*) este rareori separabilă prin praguri booleene rigide.

Sistemele convenționale de tip SIEM (Security Information and Event Management) utilizează reguli statice de corelare bazate pe condiții binare (ex. `DACĂ failed_logons > 10 ȘI time < 60s ATUNCI alertă`). Această abordare suferă de două limitări fundamentale:
1. **Rată ridicată a alarmelor false (False Positives)**: Activități administrative legitime sau procese automate de sincronizare generează depășiri izolate de prag, copleșind analiștii SOC (Security Operations Center).
2. **Fragilitate la atacuri «low-and-slow» (False Negatives)**: Atacatorii care își calibrează acțiunile imediat sub pragurile rigide de alertare scapă neobservați.

Pentru a aborda aceste limitări, lucrarea de față propune și evaluează un **Sistem de Inferență Fuzzy de tip Mamdani (FIS)** ca strat analitic avansat integrat peste arhitectura de colectare Wazuh SIEM / Sysmon.

---

## 2. Arhitectura Experimentală de Laborator

Validarea propusă este structurată în trei etape riguroase:
- **Etapa I — Validare pe Date Sintetice**: Testarea matematică și stabilitatea motorului Mamdani pe un set controlat de 500 de înregistrări structurate (200 calibrare, 100 validare, 200 test final).
- **Etapa II — Experimente Controlate în Homelab**: Rularea pe un mediu izolat de virtualizare Proxmox VE, conținând:
  - Domain Controller principal: `DC01.CORP.CYBERLAB.LOCAL` (Windows Server 2022);
  - Stații de lucru de test: `WS-CONTAB01`, `WS-HR02` (Windows 10/11 cu Sysmon);
  - Server Linux integrat în domeniu: `cyber-node01` (Ubuntu Server cu `realmd`/`sssd` și Kerberos);
  - Nod central de securitate: Wazuh Manager & Indexer 4.8.0, OPNsense Firewall cu Suricata IDS/IPS.
- **Etapa III — Integrarea cu Evenimente Reale din Wazuh**: Corelarea alertelor reale primite prin API-ul HTTP Wazuh și injectarea deciziilor în Wazuh Active Response.

```
       [ Windows Endpoints / Sysmon ]         [ Linux Domain Nodes (SSSD) ]
                     │                                       │
                     ▼                                       ▼
       ┌─────────────────────────────────────────────────────────────┐
       │             Wazuh Agents & OPNsense / Suricata              │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │             Wazuh Manager 4.8 & Wazuh Indexer               │
       │    (Colectare, Normalizare, Decodare JSON & Indexare)        │
       └──────────────────────────────┬──────────────────────────────┘
                                      │  Extracție parametri normalizați
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │          Motorul Fuzzy Mamdani (F, A, S, L → R)             │
       │   - Frecvență Autentificări (F)   - Abatere Comportament (A) │
       │   - Severitate Evenimente (S)     - Amploare Acces (L)       │
       │   => Defuzzificare Centroid: Risc R ∈ [0, 100]              │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │       Response Policy Engine (Măsuri de Siguranță)          │
       │   - Mod Simulare (Dry-Run)       - Allowlist DC01 / krbtgt  │
       │   - Aprobare Umană SOC           - Audit Log & Fail-Safe    │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
                                      ▼
                ┌─────────────────────┴─────────────────────┐
                ▼                                           ▼
       [ Wazuh Active Response ]                [ Notificare Discord Webhook ]
       (Decizie SIEM Level 3–15)                (Rich Embeds & Raport SOC)
```

---

## 3. Formalizarea Matematică a Modelului Fuzzy Mamdani

### 3.1. Variabilele Lingvistice de Intrare

Fiecare eveniment agregat $e$ este caracterizat printr-un vector de 4 caracteristici normalizate în universul de discurs $U = [0, 100]$:

1. **$F \in [0, 100]$ — Frecvența autentificărilor**: Intensitatea solicitărilor de autentificare (Kerberos TGT/TGS, NTLM) într-o fereastră temporală glisantă $\Delta t$.
2. **$A \in [0, 100]$ — Abaterea comportamentală**: Distanța statistică față de profilul istoric de referință al contului (ore de activitate, tipare de acces, geolocație/IP).
3. **$S \in [0, 100]$ — Severitatea evenimentelor**: Nivelul de risc intrinsec asociat evenimentelor raportate de Wazuh/Sysmon (ex. criptare RC4 în Kerberos `EventID 4769`, acces la `SYSVOL` `EventID 5145`, privilegii speciale `EventID 4672`).
4. **$L \in [0, 100]$ — Amploarea accesului**: Numărul și dispersia sistemelor sau resurselor atinse în domeniul Active Directory (indicator cheie pentru recunoaștere și mișcare laterală).

### 3.2. Funcțiile de Apartenență (Membership Functions)

Fiecare variabilă de intrare $X \in \{F, A, S, L\}$ este modelată prin trei termeni lingvistici: $T(X) = \{\text{scăzută}, \text{medie}, \text{ridicată}\}$.

Funcțiile de apartenență trapezoidale $\mu_{\text{trap}}(x; a, b, c, d)$ și triunghiulare $\mu_{\text{tri}}(x; a, b, c)$ sunt formalizate astfel:

$$\mu_{\text{trap}}(x; a, b, c, d) = \max\left(0, \min\left(\frac{x - a}{b - a}, 1, \frac{d - x}{d - c}\right)\right)$$

$$\mu_{\text{tri}}(x; a, b, c) = \max\left(0, \min\left(\frac{x - a}{b - a}, \frac{c - x}{c - b}\right)\right)$$

Parametrii specifici adoptați în sistem:

| Variabilă | Termen lingvistic | Tip funcție | Parametri $[a, b, c, d]$ |
| :--- | :--- | :--- | :--- |
| **$F$ (Frecvență)** | Scăzută | $\text{trapmf}$ | $[0, 0, 20, 40]$ |
| | Medie | $\text{trimf}$ | $[25, 50, 75]$ |
| | Ridicată | $\text{trapmf}$ | $[60, 80, 100, 100]$ |
| **$A$ (Abatere)** | Scăzută | $\text{trapmf}$ | $[0, 0, 15, 35]$ |
| | Medie | $\text{trimf}$ | $[25, 50, 75]$ |
| | Ridicată | $\text{trapmf}$ | $[65, 85, 100, 100]$ |
| **$S$ (Severitate)** | Scăzută | $\text{trapmf}$ | $[0, 0, 20, 40]$ |
| | Medie | $\text{trimf}$ | $[25, 50, 75]$ |
| | Ridicată | $\text{trapmf}$ | $[60, 80, 100, 100]$ |
| **$L$ (Amploare)** | Scăzută | $\text{trapmf}$ | $[0, 0, 20, 40]$ |
| | Medie | $\text{trimf}$ | $[25, 50, 75]$ |
| | Ridicată | $\text{trapmf}$ | $[60, 80, 100, 100]$ |
| **$R$ (Scor Risc)** | Scăzut | $\text{trapmf}$ | $[0, 0, 20, 34]$ |
| | Mediu | $\text{trimf}$ | $[28, 50, 69]$ |
| | Ridicat | $\text{trimf}$ | $[64, 77, 86]$ |
| | Critic | $\text{trapmf}$ | $[82, 90, 100, 100]$ |

### 3.3. Inferența Mamdani și Defuzzificarea

Pentru o regulă fuzzy $k$:
$$\text{IF } F \text{ is } A_1^k \text{ AND } A \text{ is } A_2^k \text{ AND } S \text{ is } A_3^k \text{ AND } L \text{ is } A_4^k \text{ THEN } R \text{ is } C^k$$

Forța de activare $\alpha_k$ a regulii se calculează prin t-norma minimului:
$$\alpha_k = \min\left(\mu_{A_1^k}(f), \mu_{A_2^k}(a), \mu_{A_3^k}(s), \mu_{A_4^k}(l)\right)$$

Fiecare regulă produce o mulțime fuzzy tăiată la nivelul $\alpha_k$:
$$\mu_{C'_k}(z) = \min\left(\alpha_k, \mu_{C^k}(z)\right)$$

Agregarea tuturor regulilor active $K$ se realizează prin s-norma maximului:
$$\mu_{\text{agg}}(z) = \max_{k=1,\dots,K} \mu_{C'_k}(z)$$

Scorul numeric de risc $R \in [0, 100]$ este extras prin **Defuzzificare prin Centrul de Greutate (Centroid)**:
$$R = \frac{\int_{0}^{100} z \cdot \mu_{\text{agg}}(z) \, dz}{\int_{0}^{100} \mu_{\text{agg}}(z) \, dz}$$

### 3.4. Pragurile de Decizie Experimentală

| Scor $R$ | Nivel de Risc | Decizie Operațională | Nivel Recomandat Wazuh |
| :---: | :---: | :--- | :---: |
| **$0 - 34$** | **Scăzut** | Înregistrare și monitorizare pasivă | Level 3 |
| **$35 - 69$** | **Mediu** | Alertă SOC și colectare context suplimentar | Level 8 |
| **$70 - 84$** | **Ridicat** | Alertă prioritară și propunere acțiune de contenție | Level 12 |
| **$85 - 100$** | **Critic** | Escaladare imediată și analiză izolare cont / stație | Level 15 |

---

## 4. Scenariile Experimentale de Testare

Sistemul utilizează următoarele scenarii standardizate:

- **`N01` — Autentificare normală** (*Ground Truth: Normal*): Activitate tipică de birou a unui utilizator standard.
- **`N02` — Activitate administrativă legitimă** (*Ground Truth: Normal*): Administrator de rețea care efectuează operațiuni planificate pe mai multe servere. Caracteristică critică: $L$ ridicat ($70-80$), însă $A$ scăzut ($10-15$) și $S$ scăzut ($5-15$). Sistemul fuzzy nu trebuie să declanșeze alerte false.
- **`S01` — Creștere neobișnuită a autentificărilor** (*Ground Truth: Suspect*): Vârf masiv de autentificări ($F \approx 80$), combinat cu abatere comportamentală ($A \approx 78$), tipic tentativelor de *password spraying*.
- **`S02` — Acces neobișnuit la mai multe endpoint-uri** (*Ground Truth: Suspect*): Explorare și mișcare laterală neautorizată ($L \approx 84, A \approx 80$).
- **`S03` — Evenimente de securitate cu severitate ridicată** (*Ground Truth: Suspect*): Detecție de atacuri critice din logurile Sysmon / Wazuh (Kerberoasting, DCSync, Pass-the-Hash) unde $S \ge 85$.
- **`S04` — Corelarea mai multor indicii** (*Ground Truth: Suspect*): Atac coordonat cu indicatori ridicați pe toate cele 4 dimensiuni ($F, A, S, L \ge 85$).
- **`C01` — Caz ambiguu / posibil fals pozitiv** (*Ground Truth: Ambiguu*): Mentenanță nocturnă autorizată cu anomalii ușoare de program, testând capacitatea motorului de a evita deciziile pripite.
- **`W01` — Eveniment real Wazuh** (*Ground Truth: De validat în Etapa III*): Eveniment extras din infrastructura fizică/virtuală prin conectorul HTTP `requests`.

---

## 5. Modelul de Referință (Rule-Based Baseline) și Metricile de Performanță

Pentru o comparație riguroasă conform principiilor științifice, sistemul fuzzy este comparat direct cu un clasificator clasic bazat pe reguli rigide și praguri fixe (echivalentul motoarelor SIEM tradiționale).

Clasificarea binară separă cazurile pozitive (activitate suspectă ce necesită investigație/intervenție) de cele negative (activitate legitimă/benignă).

### Formulele Metricilor:
$$\text{Precizie (Precision)} = \frac{TP}{TP + FP}$$

$$\text{Rată de Detecție (Recall)} = \frac{TP}{TP + FN}$$

$$\text{Rata Alarmelor False (FPR)} = \frac{FP}{FP + TN}$$

$$\text{Specificitate (Specificity)} = \frac{TN}{TN + FP} = 1 - FPR$$

$$F_1\text{-Score} = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

$$\text{Acuratețe (Accuracy)} = \frac{TP + TN}{TP + TN + FP + FN}$$

---

## 6. Response Policy Engine și Măsurile de Siguranță

Sistemul implementează separarea arhitecturală dintre evaluarea riscului și aplicarea măsurilor:
1. **Mod implicit de simulare (`dry-run = True`)**: Nicio modificare nu se aplică automat în infrastructură fără acord explicit.
2. **Aprobare Umană (Human-in-the-Loop)**: Măsurile de contenție pe conturi/stații necesită autorizare directă din partea analistului SOC.
3. **Allowlist pentru active și conturi critice**: Sistemele Tier-0 (`DC01`, `DC02`), conturile `krbtgt`, `Administrator` și conturile de urgență *break-glass* sunt protejate automat împotriva blocării accidentale.
4. **Acțiuni Reversibile**: Fiecare playbook Ansible sau script PowerShell/Bash generează automat comanda de rollback (`Enable-ADAccount`, curățare reguli de firewall).
5. **Mecanism Fail-Safe**: În eventualitatea unor date lipsă sau erori de parsare, sistemul recurge automat la modul sigur de monitorizare pasivă și alertare, fără intervenții distructive.
