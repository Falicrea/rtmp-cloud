# Chantier sécurité — rtmp-cloud

> Service d'authentification / orchestration MediaMTX (FastAPI). Ce document
> décrit les problèmes de sécurité identifiés et l'approche recommandée pour les
> résoudre. Il s'agit d'un chantier à part entière (changements de comportement
> et de configuration), distinct des correctifs de bugs déjà appliqués.

Date de rédaction : 2026-07-06

---

## Principe central

Le problème racine : **`idStream` sert à la fois d'identifiant public et de
crédential de publication**. Comme `idStream` apparaît dans l'URL de lecture HLS
(`/hls/{idStream}/index.m3u8`), tout spectateur connaît la clé nécessaire pour
publier sur ce même flux.

**Correction de fond : séparer le secret de publication de l'identité du stream.**

- Ajouter une colonne `publishSecret` (ou `streamKey`) à la table `Streaming`,
  générée par stream avec haute entropie (`secrets.token_urlsafe(32)`),
  **stockée hachée** (bcrypt / argon2), jamais exposée dans une URL de lecture.
- Le diffuseur configure son encodeur avec le path (`idStream`) **et** ce secret.
  MediaMTX transmet déjà ce secret dans le champ `password` / `token` du payload
  (`StreamRequest`) — il suffit de le vérifier côté service.

---

## Problèmes identifiés

| # | Gravité | Surface | Description |
|---|---------|---------|-------------|
| S1 | 🔴 Critique | `/mtx/connect` | Aucune authentification réelle : `password`/`token` jamais vérifiés, `action` jamais consultée. Un `read` passe dans la même branche qu'un `publish` et met `live=True`. |
| S2 | 🔴 Critique | `/mtx/restream`, `/mtx/disconnect` | Ouverts à tous, sans auth ni rate-limit. Permet de lancer des ffmpeg illimités, rediriger un flux vers un serveur RTMP arbitraire, et couper n'importe quel stream. |
| S3 | 🔴 Critique | Dépôt Git | `.env` est commité (`git ls-files`). Les secrets qui y sont passés vivent dans l'historique. |
| S4 | 🟠 Important | `mediamtx.yml` `runOnReady` | `bash -c '… $MTX_PATH …'` avec un path contrôlé par le client → injection shell si un path malveillant est accepté. |
| S5 | 🟠 Important | `intranet.py` | Partitionnement de base par préfixe (`sp_xxx` → base `sp`). Un préfixe deviné cible une autre base cliente. |
| S6 | 🟡 Durcissement | `mediamtx.yml`, `nginx.conf` | `apiEncryption: no`, `webrtcEncryption: no`, CORS `Access-Control-Allow-Origin: *`. |

---

## Approche par surface

### 1. `/mtx/connect` — authentifier réellement la publication (S1)
- Router sur `item.action` : seul `publish` déclenche la vérification du secret et
  la mise à `live=True` + génération de miniatures.
- Comparer `item.password` / `item.token` au hash stocké (`publishSecret`) avec une
  **comparaison à temps constant** (`hmac.compare_digest` / vérif bcrypt).
- Refuser avec **403** (et non 500) en cas d'échec — MediaMTX interprète tout
  non-200 comme un refus.

### 2. Lecture (`read`) — DÉCISION PRODUIT OUVERTE
Le comportement dépend d'un choix à trancher :
- **Streams publics** : autoriser `read` sans secret, valider que le path existe.
- **Streams privés** : exiger un **token de lecture séparé** (différent du secret de
  publication), passé en query, à durée de vie limitée (JWT signé ou token
  éphémère en base).

> ⚠️ À trancher avant l'implémentation : **publics ou privés ?** Détermine la moitié
> de la logique du hook.

### 3. Endpoints internes `/mtx/restream` et `/mtx/disconnect` (S2)
Ils sont appelés par MediaMTX depuis la même machine (`runOnReady` /
`runOnNotReady`), pas par des clients externes.
- **Bind uvicorn sur `127.0.0.1`** (ou interface privée) au lieu de `0.0.0.0`,
  et/ou exiger un header `Authorization: Bearer <MTX_INTERNAL_SECRET>` (variable
  d'env partagée).
- Ajouter un **rate-limit** sur `/restream`.
- **Allowlist des destinations RTMP** (YouTube / Twitch / Facebook…) au lieu d'une
  regex ouverte → empêche la redirection vers un serveur arbitraire (anti-SSRF).
- Passer `/mtx/disconnect` en **POST** (modifie l'état, ne doit pas être un GET
  déclenchable par une simple URL).

### 4. Injection shell dans `mediamtx.yml` (S4)
- Valider `idStream` par une **regex stricte** (ex. `^[a-z]+_[A-Za-z0-9]{6,}$`) dès
  `/mtx/connect`, avant que MediaMTX n'exécute quoi que ce soit.
- Idéalement, sortir la logique du `bash -c` vers un script recevant le path en
  **argument (`argv`)** plutôt qu'en interpolation de chaîne.

### 5. Cloisonnement des bases (S5)
- À terme, mapper le préfixe → base via une **table d'autorisation** plutôt que par
  convention de nommage.

### 6. Secrets & transport (S3, S6)
- `git rm --cached .env` + **rotation des credentials** exposés dans l'historique.
  (`configs/` est déjà non commité — OK.)
- Activer **TLS** (`apiEncryption`, `webrtcEncryption`) pour la prod.
- Restreindre le **CORS** à des origines explicites au lieu de `*`.

---

## Ordre de déploiement suggéré

1. **Immédiat / faible risque (aucun impact diffuseurs)**
   - Bind localhost + secret partagé sur `/restream` et `/disconnect`.
   - Regex stricte sur `idStream`.
   - Sortir `.env` du dépôt + roter les secrets.
2. **Cœur (nécessite régénération des clés + reconfiguration des encodeurs)**
   - Secret de publication haché + vérification par `action` dans `/mtx/connect`.
3. **Selon décision produit**
   - Politique de lecture (publique vs token de lecture).
4. **Durcissement**
   - Allowlist RTMP, TLS, CORS, table d'autorisation des bases.

---

## Notes connexes (hors périmètre strict « sécurité »)

- L'état `process_list` / `restream_list` est en dict global → **incompatible avec
  plusieurs workers uvicorn** (chaque worker a son propre dict). À migrer vers un
  store partagé (Redis) ou un worker unique dédié. Impacte la fiabilité de l'arrêt
  des process ffmpeg, donc indirectement la sécurité (process orphelins).
- Pas de gestion d'arrêt propre (`lifespan`) : les ffmpeg ne sont pas nettoyés au
  redémarrage du service.
