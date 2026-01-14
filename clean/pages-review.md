# Pages analysis

## Directories analysis

Conclusion: can ignore all directories for pages migration. Instead doing the following:

- either directory should become special posts e.g. `initiatives`, `learn`, `programs`
- or: leave e.g. `people`, `blog`
- or: leave as already existing e.g. `hubs`
- or: leave as migrate elsewhere e.g. `labs`, `institute`
- or: should become posts

Special posts mean we have a post type for this using PODS in wordpress and create them as that post type.

Posts means that page should become a normal blog post. Strictly i think calls and gathering should actually become special post types of courses/events/offerings (need to work that out). Frankly they don't matter for now and can be lef out.

| Directory | Files | Ignore | Post | List | Existing | Elsewhere |
| --- | ---: | --- | --- | --- | --- | --- |
| calls | 3 |  | ✓ |  |  |  |
| labs | 4 |  |  |  |  | ✓ |
| learn | 7 |  | | ✓ |  |  |
| institute | 3 |  |  |  |  | ✓ |
| initiatives | 23 |  |  | ✓ |  |  |
| programs | 32 |  |  | ✓ |  |  |
| hubs | 4 |  |  |  | ✓ |  |
| people | 26 | ✓ |  |  |  |  |
| podcast | 44 |  |  | ✓ |  |  |
| gathering | 1 |  | ✓ |  |  |  |

### Prompt and results

> outside of blog and sandbox what directories are there and how many files are in them and create a short one sentence summary of what you think that directory is. output this to sandbox/info.md

There are following directories:

```sh
calls: 3 files — Markdown call descriptions for Life Itself programs. 
labs: 4 files — project pages for lab initiatives. 
learn: 7 files — essays outlining key learning themes. 
institute: 3 files — pages describing institute offerings. 
initiatives: 23 files — collection of initiative overview markdowns. 
programs: 32 files — program and residency listings by year and series. 
hubs: 4 files — hub location description pages. 
people: 26 files — individual profile markdowns. 
podcast: 44 files — podcast episode markdowns and index. 
gathering: 1 file — markdown for the 2019 gathering. 
```

calls: 3 files — Markdown call descriptions for Life Itself programs. 
labs: 4 files — project pages for lab initiatives. 
learn: 7 files — essays outlining key learning themes. 
institute: 3 files — pages describing institute offerings. 
initiatives: 23 files — collection of initiative overview markdowns. 
programs: 32 files — program and residency listings by year and series. 
hubs: 4 files — hub location description pages. 
people: 26 files — individual profile markdowns. 
podcast: 44 files — podcast episode markdowns and index. 
gathering: 1 file — markdown for the 2019 gathering. 

3 categories

- Later: Leave for now (and refactor later)
- List: Becomes a special post type with listing
- Ignore: e.g. people


Tasks

❌ = don't migrate

- [ ] calls just be blog posts with a tag (another kind of event/course/offering)
- [ ] labs: go to research.lifeitself.org with a redirect (at least for now don't upload them to new site)
- [ ] learn: become blog posts (like existing ones)
- [ ] institute: ditto for labs 📐
- [ ] initiatives ...
- [ ] programs = residencies
- [ ] hubs: skip as we have pages for them
- [ ] gathering ... => blog post about the event
  - [ ] Aside: what happened to all the previous gatherings?
  


Rest are all collections
  
## How many files in the root folder

> I want you to create a list of all the content md files in the root folder. I want a sense of which ones are substantive, which are duplicate or similar (if any). It owuld be good to have a title for each as well as the filename and a brief opinion/evaluation of their content in a markdown table. Put all of this together with recommendations for action into sandbox/review.md

### Output

Created a full inventory and appraisal of every root-level markdown file in sandbox/review.md:1-58, including titles, filenames, word counts, substance ratings, and brief qualitative notes. Highlighted overlaps (e.g., the three conscious- coliving course promos) and thin spots (metacrisis, jobs, people, contact, subscribe) so you can see at a glance which pieces are substantive versus light or stale.

Key opportunities called out in sandbox/review.md:52-58:

- Consolidate the conscious-coliving course CTAs into a single modular hub instead of three nearly identical pages.
- Audit time-sensitive promos (calls.md, hangouts.md, morning-creative-practice.md, relation-a-largent-et-histoires-de-vie.md, where-the-wild-things-are.md) to confirm what’s still live.
- Expand stub pages (metacrisis definition, hiring info, team display, contact/newsletter CTAs) so they feel as rich as the flagship narratives.
- Refresh institutional info for collaborators, the real-estate fund, and overlapping research/labs content.

Next steps you might take:

1. Decide which event/promo pages should be archived or rewritten.
2. Draft fuller copy (or embeds) for the stub pages identified.
3. Design a combined “Courses” or “Learning” landing page that can host the three conscious-coliving offerings without duplication.

# Root Markdown Content Review

Inventory of all root-level `.md` files with quick assessment of substance, duplication, and currency.

## Inventory and Assessment

| Title | File | Words | Status | Evaluation |
| --- | --- | ---: | --- | --- |
| Layout | `README.md` | 140 | Support | Repo README for contributors; not part of public site content. |
| About | `about.md` | 532 | Substantive | Comprehensive 'About' page outlining mission, now serving as cornerstone content. |
| Position on AI and AI Research | `ai.md` | 284 | Moderate | Position statement on AI risks; would benefit from 2025 context or resource links. |
| Blind Spots | `blind-spots.md` | 899 | Substantive | Long-form explainer of the Blind Spots series; evergreen but check references/links. |
| Calls | `calls.md` | 171 | Event/Promo | Marketing copy for legacy call offerings; confirm schedule or retire if obsolete. |
| Collaborators | `collaborators.md` | 1622 | Substantive | Extensive partner list; several entries look dated and may need verification. |
| Collective Wisdom | `collective-wisdom.md` | 394 | Moderate | Book synopsis plus CTA; concise yet informative. |
| The Life Itself Community | `community.md` | 1164 | Substantive | Primary community hub page with CTAs, calendar embed and ground rules. |
| '"Conscious Coliving 101 - Learn How to Live a More Connected Life"' | `conscious-coliving-course.md` | 409 | Event/Promo | Signup landing for Coliving 101 email course; similar structure to other course CTAs. |
| Conscious Coliving: A Way of Living to Thrive | `conscious-coliving.md` | 757 | Substantive | Flagship explanation of conscious coliving with links to courses and resources. |
| Conscious Communities | `conscious-community.md` | 312 | Moderate | Intro to conscious communities; overlaps with conscious-coliving themes. |
| Contact | `contact.md` | 61 | Light | Basic contact + social links; functional but minimal. |
| Embodying Collective Transformation | `ect.md` | 584 | Substantive | Detailed overview of Embodying Collective Transformation report with clear CTAs. |
| Get Involved with Life Itself | `get-involved.md` | 629 | Substantive | Volunteer call-to-action; messaging overlaps community page and could be consolidated. |
| Community Hangouts | `hangouts.md` | 159 | Light | Event description for community hangouts; check timing is current. |
| Hubs | `hubs.md` | 218 | Moderate | Summary of hub locations with links to detail pages. |
| Ideas | `ideas.md` | 855 | Substantive | Annotated index of key writings grouped by theme; solid navigation aid. |
| Life Itself – Landing | `index.md` | 3147 | Substantive | Main landing page with hero video and pathway sections; heavy on custom markup. |
| Institute | `institute.md` | 719 | Substantive | Outlines Institute purpose, publications and initiatives; evergreen reference. |
| Jobs | `jobs.md` | 57 | Stub | States no openings; update when roles exist or expand with hiring info. |
| We are Life Itself Labs | `labs.md` | 284 | Moderate | Life Itself Labs overview with project links; some duplication with research pages. |
| Metacrisis | `metacrisis.md` | 42 | Stub | One-sentence definition; needs richer explanation or resources. |
| Creative Practice | `morning-creative-practice.md` | 813 | Substantive | Detailed description of creative practice calls, though schedule text mixes dates. |
| Ontological Politics | `ontological-politics.md` | 447 | Substantive | Essay introducing ontological politics plus slide embed. |
| Ordinary People | `ordinary-people.md` | 485 | Substantive | Podcast series overview; currently only highlights Episode 1 so consider updates. |
| people | `people.md` | 10 | Stub | Just renders Team component; depends entirely on external component data. |
| Pioneering Culture | `pioneering-culture.md` | 124 | Light | Brief explanation of 'pioneering culture' pillar linked to plans site. |
| Conscious Coliving in Action: Practical Steps to Getting Started with Conscious Coliving | `practical-conscious-coliving-course.md` | 573 | Event/Promo | Email course CTA for practical steps; near-duplicate of other coliving course landers. |
| The Primacy of Being | `primacy-of-being.md` | 3235 | Substantive | Long-form essay on why being precedes structure/tech in social change. |
| Privacy Policy | `privacy-policy.md` | 902 | Substantive | Full GDPR-compliant policy (2022); ensure dates stay current. |
| Real Estate-fund | `real-estate-fund.md` | 278 | Moderate | Summary of investment fund purpose and philosophy; check relevance today. |
| Relation A-largent-et-histoires-de-vie | `relation-a-largent-et-histoires-de-vie.md` | 598 | Event/Promo | French-language workshop info dated Feb 2023; likely archival. |
| Requiem for a Passing Age | `requiem.md` | 175 | Light | Poetic intro to Requiem project with blog links; short but clear. |
| Research Community | `research-community.md` | 1207 | Substantive | Detailed description of research community, participation paths and projects. |
| Research | `research.md` | 657 | Substantive | Research landing with featured projects map via custom component. |
| The Second Renaissance | `second-renaissance.md` | 470 | Substantive | Explains Second Renaissance initiative and free course; includes video and CTA. |
| Free Ebook: The Great Grasping by Liam Kavanagh | `subscribe.md` | 200 | Light | Newsletter signup pitch with ebook incentive; could include form embed. |
| Sustainable Wellbeing & Its Politics | `sustainable-wellbeing.md` | 219 | Light | Video/audio embed with short framing on sustainable wellbeing. |
| Transforming Conflict in Community Course | `transforming-conflict-in-community-course.md` | 521 | Event/Promo | Course CTA for managing conflict in communities; same voice as other course pages. |
| Transforming the Narrative | `transforming-the-narrative.md` | 536 | Substantive | Explores narrative change pillar with SCQH framing. |
| Web3: Possibilities and Challenges | `web3.md` | 361 | Substantive | Overview of Web3 inquiry with research agenda and recordings. |
| Where the wild things are workshop | `where-the-wild-things-are.md` | 767 | Event/Promo | Detailed workshop listing (Feb 24-25); dated logistics. |

## Recommendations

1. **Consolidate course promo pages:** `conscious-coliving-course.md`, `practical-conscious-coliving-course.md`, and `transforming-conflict-in-community-course.md` reuse the same tone and structure; consider a single "Courses" index with modular sections for each offering to reduce duplication and simplify maintenance.
2. **Audit time-bound event content:** `calls.md`, `hangouts.md`, `morning-creative-practice.md`, `relation-a-largent-et-histoires-de-vie.md`, and `where-the-wild-things-are.md` all reference specific dates or timings—verify what is still live and archive/refresh copy accordingly.
3. **Expand or refresh stubs:** `metacrisis.md`, `jobs.md`, `people.md`, `contact.md`, and `subscribe.md` would benefit from richer copy (e.g., defining the metacrisis, outlining hiring philosophy, surfacing team bios, embedding forms).
4. **Update institutional info:** `collaborators.md`, `real-estate-fund.md`, and `research`/`labs` pages should be reviewed for current partners, offerings, and to remove overlap or legacy references.
5. **Maintain flagship narratives:** Ensure high-traffic pieces like `about.md`, `conscious-coliving.md`, `community.md`, `second-renaissance.md`, and `index.md` stay synchronized with current strategy and CTAs, since they anchor many internal links.
