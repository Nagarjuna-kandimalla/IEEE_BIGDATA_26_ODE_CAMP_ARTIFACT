# Paper-specific artifact scope

The root README is the reproduction entry point and experiment-to-file map.

The release retains W2 (downstream selective-auditing replay), W3 (mapped-access ablation), W5 (paired audit-cost accounting), the four-feature ablation, and the four-stage Bowtie2 live experiment. Their fixed cohorts, expected predictions, causal histories, model code and checks are included. Auxiliary route checks within the feature package establish the distinction between native configurations and feature-only comparisons.

The six-workflow offline cohort is needed to rebuild the no-Bowtie2 initial model. It remains even though the six original workflows are not rerun in this paper. Only Bowtie2 and common workflow helpers are executable workflow entries here.

Removed from this release: WORKS-only RQ1-RQ4 evaluation suites and plots; W1 matched-budget comparison; Ponder adapter; unrelated workflow launchers; older cold/warm records and plots; obsolete manuscript versions. Earlier Git commits preserve their history. Retained historical provenance documents describe the original import and do not define current contents.

The current paper source is `Big_Data_paper/Big_Data_Camera_Ready/source/Camera_Ready_Introduction_Revision`. Its Section II and scientific wording are preserved; Table I/II bodies now load the same values from generated, verified row files.
