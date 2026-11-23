# Hack The Box

Retour à l'[index des writeups](../README.md)

Machines résolues sur [Hack The Box](https://www.hackthebox.com/), classées dans `Machines/<NomMachine>/`.

Cette section est **ouverte** : aucun writeup n'y est encore publié, et c'est le meilleur endroit
pour une première contribution. Une machine vous a bloqué une soirée ? C'est exactement le writeup
qui manque à quelqu'un d'autre.

## Par où commencer

- **[Méthode](METHODE.md)** — la démarche complète, du premier `nmap` au root, avec la grille de
  rédaction attendue. À lire avant d'attaquer sa première machine.
- **Parcours conseillé** ci-dessous : des machines retirées, classées par compétence, pour
  progresser sans tomber sur du *Insane* dès la deuxième.
- **[Modèle de writeup](../_template/README.md)** et assistant `python3 scripts/new_writeup.py`.

## Parcours conseillé

Machines retirées (*retired*), donc publiables. La colonne « compétence » dit ce que la machine
travaille, sans dévoiler le chemin — l'ordre suit une progression réaliste, pas la difficulté
affichée par HTB.

### Fondations Windows (2017)

| Machine | OS | Difficulté | Compétence |
| --- | --- | --- | --- |
| [Blue](https://app.hackthebox.com/machines/Blue) | Windows | Easy | SMB, énumération de version, exploitation d'un service obsolète |
| [Legacy](https://app.hackthebox.com/machines/Legacy) | Windows | Easy | SMB sous Windows XP/2003, `searchsploit` |
| [Devel](https://app.hackthebox.com/machines/Devel) | Windows | Easy | FTP anonyme, dépôt de webshell ASPX, IIS |
| [Optimum](https://app.hackthebox.com/machines/Optimum) | Windows | Easy | Serveur de fichiers HTTP vulnérable, `nishang` |
| [Jerry](https://app.hackthebox.com/machines/Jerry) | Windows | Easy | Tomcat, gestionnaire d'applications, déploiement de WAR |
| [Grandpa](https://app.hackthebox.com/machines/Grandpa) | Windows | Easy | IIS 6, WebDAV, `davtest` |
| [Granny](https://app.hackthebox.com/machines/Granny) | Windows | Easy | WebDAV en écriture, contournement de méthode HTTP |

### Linux, services et web historique

| Machine | OS | Difficulté | Compétence |
| --- | --- | --- | --- |
| [Lame](https://app.hackthebox.com/machines/Lame) | Linux | Easy | Samba 3.0.20, `searchsploit`, premier shell |
| [Bashed](https://app.hackthebox.com/machines/Bashed) | Linux | Easy | Webshell PHP déposé, cron root, `sudo` |
| [Nibbles](https://app.hackthebox.com/machines/Nibbles) | Linux | Easy | CMS avec upload, `sudo` sur script |
| [Networked](https://app.hackthebox.com/machines/Networked) | Linux | Easy | Upload PHP, contournement de filtre, cron |
| [Mirai](https://app.hackthebox.com/machines/Mirai) | Linux | Easy | Identifiants par défaut, fichier supprimé récupérable |
| [Shocker](https://app.hackthebox.com/machines/Shocker) | Linux | Easy | CGI, Shellshock, `sudo` |
| [FriendZone](https://app.hackthebox.com/machines/FriendZone) | Linux | Easy | SMB, transfert de zone DNS, LFI, cron |
| [Beep](https://app.hackthebox.com/machines/Beep) | Linux | Easy | Elastix, LFI, Webmin, plusieurs chemins possibles |

### Web moderne (2022-2025)

| Machine | OS | Difficulté | Compétence |
| --- | --- | --- | --- |
| [Soccer](https://app.hackthebox.com/machines/Soccer) | Linux | Easy | Vhosts, gestionnaire de fichiers, injection SQL |
| [Busqueda](https://app.hackthebox.com/machines/Busqueda) | Linux | Easy | Application Flask, `eval` Python, `sudo` sur script |
| [Pilgrimage](https://app.hackthebox.com/machines/Pilgrimage) | Linux | Easy | Fuite de dépôt Git, `git-dumper`, traitement d'images |
| [CozyHosting](https://app.hackthebox.com/machines/CozyHosting) | Linux | Easy | Spring Boot Actuator, session volée, injection de commandes |
| [Keeper](https://app.hackthebox.com/machines/Keeper) | Linux | Easy | Request Tracker, identifiants par défaut, base KeePass |
| [Analytics](https://app.hackthebox.com/machines/Analytics) | Linux | Easy | Metabase, CVE récente, réutilisation d'identifiants |
| [Sau](https://app.hackthebox.com/machines/Sau) | Linux | Easy | SSRF, `request-baskets`, injection de commandes |
| [PermX](https://app.hackthebox.com/machines/PermX) | Linux | Easy | Chamilo, LFI, `sudo` sur script |
| [BoardLight](https://app.hackthebox.com/machines/BoardLight) | Linux | Easy | Dolibarr, CVE, binaire SUID |
| [Sea](https://app.hackthebox.com/machines/Sea) | Linux | Easy | WonderCMS, thème piégé, hash à casser |
| [LinkVortex](https://app.hackthebox.com/machines/LinkVortex) | Linux | Easy | Ghost, `git-dumper`, injection de commandes |
| [Editor](https://app.hackthebox.com/machines/Editor) | Linux | Easy | XWiki, CVE récente, énumération de vhosts |

### Active Directory

| Machine | OS | Difficulté | Compétence |
| --- | --- | --- | --- |
| [Forest](https://app.hackthebox.com/machines/Forest) | Windows | Easy | AS-REP roasting, `rpcclient`, ACL |
| [Active](https://app.hackthebox.com/machines/Active) | Windows | Easy | GPP dans SYSVOL, `gpp-decrypt`, Kerberoasting |
| [Sauna](https://app.hackthebox.com/machines/Sauna) | Windows | Easy | `ldapsearch`, AS-REP, DCSync |
| [Support](https://app.hackthebox.com/machines/Support) | Windows | Easy | LDAP, service .NET, reverse d'un binaire, `BloodHound` |
| [Resolute](https://app.hackthebox.com/machines/Resolute) | Windows | Medium | Pulvérisation de mots de passe, `rpcclient`, DLL |
| [Monteverde](https://app.hackthebox.com/machines/Monteverde) | Windows | Medium | Azure AD Connect, `BloodHound`, `WinRM` |
| [Cascade](https://app.hackthebox.com/machines/Cascade) | Windows | Medium | LDAP, VNC chiffré, restauration AD |
| [Escape](https://app.hackthebox.com/machines/Escape) | Windows | Medium | MSSQL, `xp_cmdshell`, certificats |
| [Certified](https://app.hackthebox.com/machines/Certified) | Windows | Medium | ADCS, `BloodHound`, `WriteOwner` |
| [Administrator](https://app.hackthebox.com/machines/Administrator) | Windows | Medium | `netexec`, `BloodHound`, `evil-winrm` |

### Autres systèmes et palier supérieur

| Machine | OS | Difficulté | Compétence |
| --- | --- | --- | --- |
| [Sunday](https://app.hackthebox.com/machines/Sunday) | Solaris | Easy | `finger`, cassage de hash, `sudo` sur `wget` |
| [Poison](https://app.hackthebox.com/machines/Poison) | FreeBSD | Medium | LFI, empoisonnement de logs, tunnel VNC |
| [SolidState](https://app.hackthebox.com/machines/SolidState) | Linux | Medium | Serveur de mail James, évasion de `rbash` |
| [Haircut](https://app.hackthebox.com/machines/Haircut) | Linux | Medium | Upload PHP, injection de commandes, `screen` |
| [Nineveh](https://app.hackthebox.com/machines/Nineveh) | Linux | Medium | Vhosts, `phpLiteAdmin`, élévation par `chkrootkit` |
| [Blackfield](https://app.hackthebox.com/machines/Blackfield) | Windows | Hard | AD, `BloodHound`, abus d'ACL, `lsass` |
| [Sizzle](https://app.hackthebox.com/machines/Sizzle) | Windows | Insane | SMB, FTP, certificats, Kerberos |

## Ce qu'on attend d'un writeup HTB

Une checklist courte, celle qui distingue une note personnelle d'un writeup publiable :

- [ ] les **deux scans** (`-sC -sV` puis `-p-`), avec la sortie utile seulement ;
- [ ] la **version exacte** de chaque service exploité ;
- [ ] au moins une **impasse documentée** : ce qui a été essayé sans succès ;
- [ ] la **commande exacte** de l'accès initial, et la sortie qui prouve le shell ;
- [ ] le chemin utilisateur puis le chemin root, séparés ;
- [ ] les **flags tronqués** (`HTB{...}`), jamais en clair ;
- [ ] une section **Leçons** : ce qui a coûté du temps ;
- [ ] des captures **seulement** pour ce qui est illisible en texte.

## Règles de la section

- **Original uniquement.** Un writeup se rédige à partir de *sa* session. Recopier un writeup
  publié ailleurs (0xdf, IppSec, un blog) pose un problème de droit d'auteur — ces textes ne sont
  pas sous licence libre — et vide la contribution de son intérêt. Lire, comparer, comprendre :
  oui ; copier : non.
- **Machine active → `status: draft`.** On publie une fois la machine retirée.
- **Pas de contenu qui casse le jeu** : pas de flag complet, pas de solution d'une machine du
  pool actif.

## Machines publiées

<!-- INDEX:START -->

| Machine | OS | Difficulté | Auteur | Date | Writeup |
| --- | --- | --- | --- | --- | --- |
| _aucun writeup publié pour le moment_ |  |  |  |  |  |

<!-- INDEX:END -->

## Ajouter une machine

Depuis la **racine du dépôt** :

```bash
python3 scripts/new_writeup.py     # assistant : pose les questions et crée le dossier
```

Ou à la main :

```bash
cp -r writeups/_template writeups/hackthebox/Machines/nom-machine
$EDITOR writeups/hackthebox/Machines/nom-machine/README.md
python3 scripts/update_index.py
```

Chaque dossier contient le writeup (`README.md`) et ses captures (`assets/`).
La machine n'apparaît ci-dessus qu'une fois son frontmatter passé en `status: published`.
