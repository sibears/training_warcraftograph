# WarCraft-o-Graph

WarCraft-o-Graph is a training service created by part of SiBears team. 

WarCraft-o-Graph is a simple get/put secret storage based on Python Flask.
The core idea: give a single service with lot of vulns (in contrast to common 1-2).

Upd. (2021). Note, that fix/attack balance is totally broken, so it's mostly 
find & fix race. Consider using of prepared services bundles (Warchief's services)
to allow players to attack more vulns.

### Vulnerabilities:
  - Hardcoded key
  - Weak id generation
  - Typo leading to SQL injection
  - Unescaped input at LIKE statements
  - Path traversal leading to DB exposure (+key reveal)
  - Wrong usage of bcrypt function
  - Mb some another vulns

### Contain:
  1. warcraftograph -- secret encoding\decoding service
  2. service -- service files that should be given to participants
  3. jury (Warchief's) services:
     * serviceBloodhoof -- fixed hashes but has some SQL vulns.
     * serviceVoljin -- fixed SQL but has unchanged WARCHIEF_SECRET
     * serviceThrall -- the only vuln (we hope) is wrong bcrypt usage
  4. checker.py -- checker file for [that](http://ctf.hcesperer.org/gameserver/) jury system
  5. IconsHD -- folder with highres icons and PSD file with service logo
  6. Achievments -- folder with nice wow-like achievments according to main goals in the training

### Authors:
  * Anna Zueva -- Frontend
  * Irina Borovkova -- Warcraftograph module
  * Nikita Oleksov -- Checker and testing
  * Oleg Broslavsky -- Backend
