# Component ownership inventory

- **Konstellation** — UI, fleet navigation, existing Lens/query/renderers, selected-Kristal browsing, Reader Policy and route authentication.
- **Kompiler** — read-only query engine, Context Packs and optional v6 projections when an appropriate v7 Surface is available. No general v9/v10-to-v6 transformation is implied.
- **Kristal Framework** — normative logical identity, deterministic commitments, v9 state architecture and v10 host profiles.
- **Authoring Kit** — authoring, local checks, builds, AI read-surface production; selected local CLI commands are delegated rather than reimplemented.
- **Manager** — authoritative local **instance inventory** and operational sync (subject to qualification and visibility permissions).
- **Bootstrap / C1 / C2 / C3** — node setup, independent qualification, visibility grants and verified collection/release controls.
- **Arketype** — design-only archetype registry and templates. Neither operational registry nor authority over actual Kristals.
- **Konstellation Light** — approved public static read view, distinct from the desktop/global inventory browser.
- **SemantiK** — optional separately qualified language realization profile; not an inventory or publication authority.
- **Alfresco** — optional external-document source whose access controls apply before any reading or Context Pack.

**Rule:** Reader projections and protocol integrity do not equal domain truth, logical commitment, approval, public authorization or activation. This pack remains a narrow compatibility aid.


## Alignement v11 (Integration Pack 0.3.0-alpha.1)

Le pack ne devient ni registre d'instances (Manager), ni autorité canonique (Framework/Kit), ni gouverneur de dictionnaires (diK). Il peut **refuser** un échange diK → Kit qui viole les SHA-256, espaces de noms ou correspondances, et fabriquer une lecture dérivée non canonique. Le Framework draft.4 reste l'autorité de validation; l’Authoring Kit draft.3 reste l’autorité pour importer, enregistrer et sélectionner un catalogue.
