Replace this file in the existing PC_database repository:

  site/assets/app.js

Sorting behavior after this patch:
- Conference view: year groups; papers within each year are ordered by starting page.
- Year view: conference groups; papers within each conference are ordered by starting page.
- Search / Tag / Home lists: year descending, conference, then starting page.
- Surveys: year descending, then starting page.
- If pages is absent or tied, source BibTeX file/order is used as fallback.
