Elements: keep 2, change 2, new 3, remove 2. `replace` and `decide` are judgements the comparison does not make: mark them in the transition TXT where a new element replaces a removed one or a choice is open.

| Type | Element | Change | Detail |
|------|---------|--------|--------|
| capability | Ticketing | keep |  |
| capability | Account-based travel | new |  |
| asset | Account-based ticketing platform | new |  |
| asset | Open-loop payment gateway | new |  |
| asset | Legacy fare engine | remove |  |
| asset | Card personalisation service | remove |  |
| process | Fare change | change | description changed |
| organisation | Platform team | keep |  |
| product | Acme app | change | description changed |

| Core link | Verb | Change | Detail |
|-----------|------|--------|--------|
| capability → asset | requires | keep |  |
| process → capability | realises | keep |  |
| organisation → capability | has | keep |  |
| product → capability | requires | new |  |
