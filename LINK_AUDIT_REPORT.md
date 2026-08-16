# Paper-link audit report

Audit base: successful GitHub Pages artifact for commit `3dc52ac8fd0b5bb1ed14a734ab3cb1fa835f0121`.

- Conference papers audited: **4294**
- Conferences represented: **58**
- `10.5555` records: **132**
- Affected conferences: **AAMAS 50**, **SODA 32**, **IJCAI 29**, **ICML 7**, **NeurIPS 7**, **AAAI 6**, **SOFSEM 1**
- Missing `primaryUrl` before patch: **18**; **17** are recoverable from `DBLP:` keys.

## Affected conference-years

- **AAAI**: 2006 (1), 2007 (2), 2008 (3)
- **AAMAS**: 2009 (1), 2010 (1), 2013 (3), 2014 (2), 2015 (6), 2016 (1), 2017 (4), 2018 (2), 2019 (3), 2020 (6), 2021 (3), 2022 (7), 2023 (4), 2024 (3), 2025 (4)
- **ICML**: 2020 (1), 2023 (2), 2025 (4)
- **IJCAI**: 2003 (2), 2005 (4), 2007 (2), 2009 (7), 2013 (7), 2015 (5), 2016 (2)
- **NeurIPS**: 2015 (1), 2018 (1), 2019 (2), 2020 (2), 2021 (1)
- **SODA**: 1998 (4), 1999 (2), 2000 (2), 2001 (5), 2002 (1), 2003 (2), 2004 (5), 2005 (2), 2006 (5), 2007 (2), 2008 (2)
- **SOFSEM**: 1998 (1)

## Result after patch

- Ordinary DOI links remain unchanged.
- Test/unmaintained DOI prefixes never use `doi.org` as the paper destination.
- Existing ACM / IFAAMAS / IJCAI / AAAI / PMLR / DBLP URLs are preferred for those records.
- A `DBLP:` BibTeX key is used as the final deterministic fallback.
- One current item remains deliberately unlinked: `IWOCA 2007 / Suchy2008SeidelSwitching`, because no verified direct conference-paper destination was found.
