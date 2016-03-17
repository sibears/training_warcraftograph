# WarCraft-o-Graph

WarCraft-o-Graph is a training service created by part of SiBears team. Service is based on Python Flask.

### Vulnerabilities:
  - Weak id generation
  - Typo leading to SQL injection
  - Unescaped input at LIKE statements
  - Hardcoded key
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

 ### Authors:
    * Anna Zueva -- Frontend
    * Irina Borovkova -- Warcraftograph module
    * Nikita Oleksov -- Checker and testing
    * Oleg Broslavsky -- Backend
