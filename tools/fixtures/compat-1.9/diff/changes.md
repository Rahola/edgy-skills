Elements: keep 39, change 1, new 0, remove 0. `replace` and `decide` are judgements the comparison does not make: mark them in the transition TXT where a new element replaces a removed one or a choice is open.

| Type | Element | Change | Detail |
|------|---------|--------|--------|
| purpose | Everyone can travel without a car | keep |  |
| story | Your city, on time | keep |  |
| content | Live departures | keep |  |
| capability | Fare product definition | keep |  |
| capability | Sales in every channel | keep |  |
| capability | Validation and inspection | keep |  |
| capability | Timetable planning | keep |  |
| capability | Real-time passenger information | keep |  |
| capability | Revenue settlement | keep |  |
| asset | Fare engine | keep |  |
| asset | Ticket shop | keep |  |
| asset | Inspection app | change | hosting changed; time changed |
| asset | Timetable planner | keep |  |
| asset | Passenger info hub | keep |  |
| asset | Settlement system | keep |  |
| asset | Integration platform | keep |  |
| asset | Fare rules | keep |  |
| asset | Trip events | keep |  |
| asset | Timetable | keep |  |
| asset | Sales ledger | keep |  |
| process | Plan services | keep |  |
| process | Plan the network | keep |  |
| process | Publish timetables | keep |  |
| process | Sell travel | keep |  |
| process | Price fare products | keep |  |
| process | Sell in every channel | keep |  |
| process | Run services | keep |  |
| process | Inspect tickets | keep |  |
| process | Settle revenue | keep |  |
| process | Allocate revenue to operators | keep |  |
| task | Buy a ticket | keep |  |
| channel | Mobile app | keep |  |
| journey | Daily commute | keep |  |
| organisation | Transit authority | keep |  |
| organisation | Fares team | keep |  |
| organisation | Platform team | keep |  |
| organisation | Inspection unit | keep |  |
| product | Season ticket | keep |  |
| brand | Acme Transit | keep |  |
| people | Ticket inspector | keep |  |

| Core link | Verb | Change | Detail |
|-----------|------|--------|--------|
| organisation → capability | has | keep |  |
| capability → asset | requires | keep |  |
| process → capability | realises | keep |  |

| Relationship | Verb | Change | Detail |
|--------------|------|--------|--------|
| CAP-05 → APP-05 | requires | keep |  |
| CAP-05 → APP-07 | requires | keep |  |
| CAP-06 → APP-06 | requires | keep |  |
| CAP-08 → APP-11 | requires | keep |  |
| CAP-09 → APP-17 | requires | keep |  |
| CAP-10 → APP-20 | requires | keep |  |
| CAP-05 → APP-16 | requires | keep |  |
| CAP-09 → APP-16 | requires | keep |  |
| APP-07 → DAT-01 | stores | keep |  |
| APP-06 → DAT-02 | stores | keep |  |
| APP-11 → DAT-03 | stores | keep |  |
| APP-05 → DAT-04 | stores | keep |  |
| APP-07 → APP-05 | transfers | keep |  |
| APP-06 → APP-20 | transfers | keep |  |
| APP-11 → APP-17 | transfers | keep |  |
| APP-05 → APP-20 | transfers | keep |  |
| PRO-10 → PRO-11 | contains | keep |  |
| PRO-10 → PRO-12 | contains | keep |  |
| PRO-20 → PRO-21 | contains | keep |  |
| PRO-20 → PRO-22 | contains | keep |  |
| PRO-30 → PRO-32 | contains | keep |  |
| PRO-50 → PRO-51 | contains | keep |  |
| PRO-11 → CAP-08 | realises | keep |  |
| PRO-12 → CAP-08 | realises | keep |  |
| PRO-21 → CAP-04 | realises | keep |  |
| PRO-22 → CAP-05 | realises | keep |  |
| PRO-32 → CAP-06 | realises | keep |  |
| PRO-51 → CAP-10 | realises | keep |  |
| PRO-21 → DAT-01 | accesses | keep |  |
| PRO-22 → DAT-01 | accesses | keep |  |
| PRO-22 → DAT-04 | accesses | keep |  |
| PRO-32 → DAT-02 | accesses | keep |  |
| PRO-51 → DAT-04 | accesses | keep |  |
| PRO-12 → DAT-03 | accesses | keep |  |
| ORG-02 → PRO-21 | performs | keep |  |
| ORG-02 → PRO-22 | performs | keep |  |
| ORG-04 → PRO-32 | performs | keep |  |
| ORG-01 → PRO-51 | performs | keep |  |
| ORG-03 → PRO-12 | performs | keep |  |
| ORG-01 → PRO-11 | performs | keep |  |
| PRO-21 → APP-07 | requires | keep |  |
| PRO-22 → APP-05 | requires | keep |  |
| PRO-32 → APP-06 | requires | keep |  |
| PRO-51 → APP-20 | requires | keep |  |
| PRO-12 → APP-11 | requires | keep |  |
| PRO-11 → APP-11 | requires | keep |  |
| ORG-02 → CAP-04 | has | keep |  |
| ORG-02 → CAP-05 | has | keep |  |
| ORG-04 → CAP-06 | has | keep |  |
| ORG-03 → CAP-08 | has | keep |  |
| ORG-03 → CAP-09 | has | keep |  |
| ORG-01 → CAP-10 | has | keep |  |
| PEO-01 → APP-06 | interacts with | keep |  |
| PRD-01 → CAP-05 | requires | keep |  |
| ORG-02 → APP-07 | manages | keep |  |
| ORG-02 → APP-05 | manages | keep |  |
| ORG-03 → APP-11 | manages | keep |  |
| ORG-03 → APP-17 | manages | keep |  |
| ORG-03 → APP-16 | manages | keep |  |
| ORG-04 → APP-06 | manages | keep |  |
| ORG-01 → APP-20 | manages | keep |  |
| CAP-04 → APP-06 | requires | new |  |
| CAP-04 → APP-07 | requires | remove |  |
