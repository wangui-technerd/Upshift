# Student-focused expansion

Reviewed 13 November 2026. Added 19 distinct sourced records to the previous 43, for 62 total. All 19 additions are Kenya-based or explicitly Kenya-eligible. Short summaries are paraphrases; blank skills and unknown dates are deliberate.

## Availability and audience

- 10 additions are candidate adverts awaiting employer verification. They are exported separately in student_expansion_candidates.json.
- 7 additions are archived references: BURN QA, Urgent Action Fund-Africa ICT/database, Zade audit, Kenya Tradex cybersecurity, SENRI BI, Amref reporting, and PZ Cussons marketing.
- 2 additions have unresolved availability: One Acre Fund ITSM and CorpsAfrica communications. Secondary adverts remain visible, but original endpoints returned 404 and 410 respectively.

The candidate subset includes software development, data analytics, enterprise systems, IT support, digital marketing, procurement and a continuing-student ICT attachment. It is a review queue, not proof that every applicant qualifies. A degree-completion requirement still excludes some continuing students. Kobby is one multi-department programme record, not nine separate vacancies.

## Source conflicts

Cellulant, One Acre Fund, Sucafina and LOLC adverts have conflicting secondary deadlines; their deadlines remain unknown. CorpsAfrica's reported future deadline does not override a gone employer endpoint. BURN's original page returned HTTP 410, so its entry is archived despite future secondary dates. PZ Cussons' employer search index gave 6 November, which takes precedence over later secondary dates; the full employer page was unreadable.

## Rejected leads

The [Terra Softech career directory](https://www.terrasoftech.com/open-career/) lists nine technical internships. These were inspected but excluded from the dataset expansion:

| Source | Reason for exclusion |
| --- | --- |
| [Mobile developer](https://www.terrasoftech.com/mobile-app-developer-3-month-intern/) | Internship title but at least four years of IT experience; advert does not confirm Kenyan location. |
| [Backend developer](https://www.terrasoftech.com/backend-developer-3-week-intern/) | Directory says three months, detail title says three weeks, body says 12 weeks in summer 2026. |
| [Data engineer](https://www.terrasoftech.com/data-engineer-3-month-intern/) | Body refers to an internship experience at Tesla on another employer's page; employer attribution unclear. |
| Other six directory internship entries | Excluded from this batch pending clarification of directory quality, location and current intake dates. |

This does not establish that the employer is illegitimate; it means those pages are insufficient for trustworthy recommendations.

## Validation and next use

The generator enforces 62 unique source URLs and stable unique IDs. The separate review subset excludes every archived or availability-unverified addition.

The Android app now bundles those 10 candidates in app/src/main/assets/opportunities.json and uses them for guests and signed-in users. Cards and detail screens identify unconfirmed availability, and details include the source link, collection date, reported deadline and eligibility notes. Archived, unresolved, unsourced and past-deadline entries are filtered out. Source-mentioned skill tags may include alternatives or preferred tools, so coverage is not proof of qualification. Unknown duties and requirements are not invented.

No Firestore write has been performed. Firestore adverts supplement the bundle; a matching ID overrides it, including an archived status used to withdraw a bundled role. Run `python scripts/prepare_listing_catalogue.py` to rebuild both research exports and the bundled candidates. An app rebuild is required after changing the bundle. Full-catalogue entries have not all been approved for the app feed.
