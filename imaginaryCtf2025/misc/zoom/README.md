zoom (misc) — Writeup

- File: `beavertail.png`
- Goal: From the image only, find the exact pond with the red dot and submit its coordinates.

**Idea (image geolocation)**
- Wingtip logo → Air Canada → likely Canada.
- A large river/lake in the background and a sweeping highway interchange beside a golf course.
- Searching Ottawa’s west end on satellite maps, the highway curve matches ON‑416 near Fallowfield Rd and the adjacent golf course layout matches Cedarhill Golf and Country Club.
- The red dot corresponds to the small pond at the south‑east edge of the course.

**Reproduce**
- Rotate the image so the highway runs bottom‑left → top‑right.
- On Google Maps/OSM, inspect south‑west Ottawa. Find ON‑416’s curve near Fallowfield Rd; a golf course sits east of the highway with several ponds.
- Match fairway/pond shapes to confirm Cedarhill Golf and Country Club.
- Drop a pin on the south‑east pond (where the red dot is in the photo).

**Result**
- Target pond center (pin): approximately `45.2814975, -75.7949382`.
- OSM link: https://www.openstreetmap.org/?mlat=45.2814975&mlon=-75.7949382#map=17/45.2814975/-75.7949382

**Flag**
```
ictf{45.281,-75.795}
```



