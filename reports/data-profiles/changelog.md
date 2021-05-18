# Changes into v5

## Major changes

- changed the stage where some files are exported
- integrated first stage data processing and uploads to osf to this repo
- player with next touch calculation moved
- [data profiles](./index.html) automatically generated with upload


## Minor changes
- fill missing transfermarkt teams
- novel entity coreference matching
- new seasons (222 from 102)
  - seasons that have no more than 5 missing coreferences in all the lineups are included
- fix cup / league differentiation bug based on transfermarkt competition category (compform column)
- checked worst looking matches among players
  - e.g:
    - https://www.whoscored.com/Players/409334/Show/x 
    - https://www.transfermarkt.com/x/profil/spieler/809639
    