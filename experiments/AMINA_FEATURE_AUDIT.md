# Amina feature audit

Production approval: **not granted**. The head study and body remain separate.

| Feature | Cause | Action | Remaining work |
|---|---|---|---|
| Eyes, iris, pupil and reflections | Old dimensions and depths did not fit the anatomy head | Eye components refitted together; closed socket cavities tested after rejecting boundary projection | Lid silhouette, expression and deformation need reference review |
| Scalp and hairline | Old scalp shape caused detached side strips and incorrect forehead fit | Old scalp pieces removed; cap and swept native fibres built from evaluated head surface | Straight fibre appearance and hairline styling still differ from reference |
| Puffs | Geometry and transforms were unchanged despite the new head | Support meshes and native strands fitted together, with unequal sizes; hair shader changed | Curl clumping and silhouette still too patterned |
| Headband and bow | Unchanged band was wider than the head; bow position was inherited | Band rebuilt from head-surface samples; whole bow fitted using its knot attachment | Fabric detail and clearance require final visual review |
| Earrings | Name-filter import omitted four stud/bead objects; stems retained old ear locations | All six objects restored and fitted to new ear positions; bead material corrected to purple | Fine attachment and motion unverified |
| Nose, cheeks, jaw, ears | Anisotropic anatomical mapping and generic proportions; not a transfer-only defect | Forehead and lower-face proportions adjusted; nose width refined | Custom Amina sculpt likeness remains incomplete |
| Mouth and teeth | New mouth placement and boundary projection failed; the first cavity workflow left the lips intact. Exact contributions of operand shape and dependency order remain unverified. | Mouth opening repositioned; closed cavity construction tested after folded-lip projection was rejected | Lip volume, tongue, individual tooth detail and expression shapes incomplete |
| Skin and shading | Materials were not consistently matched to the reference | Warm brown anatomy material retained for review; earrings corrected | Skin colour, roughness and lighting must be evaluated consistently against reference |
| Body and hands | Earlier modelling limitations; not newly transferred into this head | Source geometry audited; no nonfinite or overused edges found in selected body-feature meshes | Hand anatomy, nail placement, neck integration, posing and deformation require work |
| Clothes, flower, buttons, shoes | Existing simplified garment construction and incomplete fitting | 27 body-feature objects audited; reference colours and key motifs present | Cloth silhouette, bib construction, stitching, shoe detail, clearance and deformation unverified |

## Verification

Source geometry hashes and world transforms were compared. Body-feature geometry was audited. Three head views were rendered and PNG integrity checked. Finite coordinates and mesh-edge checks do not establish visual likeness, cloth clearance or deformation quality.

Scripts in this folder are archives of Windows project experiments. They require the corresponding local input blend files, approved reference and png_validation.py; this folder is not a standalone production pipeline.