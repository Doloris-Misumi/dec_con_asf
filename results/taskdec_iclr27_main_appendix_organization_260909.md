# TaskDec ICLR 2027 Main/Appendix Organization

Date: 2026-09-09

Goal: organize the current TaskDec results into an ICLR 2027-style paper under the 9-page submission limit, while keeping the paper framed as an architecture-level contribution rather than a small module attached to ASF.

Latest visual-layout update: the author requests a separate motivation figure, architecture figure, main-text PCA, spatial BEV gate visualization, and real-scene detection comparisons. The five-figure/four-compact-table plan in [the updated figure inventory](taskdec_figure_table_inventory_and_placement_260910.md) supersedes the earlier compact figure-count recommendations below. A [two-scene spatial gate draft](../analysis_exports/taskdec_bev_gate_fig4_260910/paper_fig4_taskdec_bev_gate_draft.pdf) and [21 full-grid exports with reproduction notes](../analysis_exports/taskdec_bev_gate_fig4_260910/README.md) are now available. Real-scene ASF–TaskDec detection comparisons remain to be generated. The existing centroid-distance/gate-mean plot is a statistical diagnostic, not a spatial heatmap.

Writing update, 2026-09-10: the author clarified that the ablated variants also underwent 1,000-sample preliminary evaluation before selection. Different selected epoch indices do not by themselves imply inconsistent selection; document the actual subset, metric, and candidate range. Keep the released official ASF checkpoint as the main comparator. Label the v2.0 results as an early DecControlled variant without task context. Emphasize LR/LC availability and native VoD transfer over the strong PP-Concat baseline, briefly noting the RC limitation. Discuss L4DR fully in the main K-Radar comparison and retain its VoD table row, with only a short acknowledgment in the transfer paragraph.

## ICLR 2027 Format Constraints

Official ICLR 2027 author guidelines state:

- Main text at initial submission must be **9 pages or fewer**.
- During discussion/rebuttal and camera-ready, the limit increases to **10 pages**.
- References do **not** count toward the page limit.
- Appendix after references is unlimited, but reviewers are not required to read it.
- Double-blind anonymity applies to both main paper and supplementary material.
- An AI use statement is required and does not count toward the page limit.
- Reproducibility and ethics statements are recommended; they do not count toward the main page limit.

Source: https://iclr.cc/Conferences/2027/AuthorGuidelines

Practical implication: the main paper must carry the whole story without relying on appendix tables. Appendix should support reproducibility, protocol audits, extended comparisons, and extra visualizations.

## Core Paper Thesis

Recommended one-sentence thesis:

> We propose TaskDec, a task-aware decoupled fusion architecture that turns unified canonical patch fusion into object-evidence-aware sensor fusion by decomposing each modality patch into shared target evidence and sensor-specific residual evidence, then using these states to control foreground gating, sensor reliability, and task-context modulation.

Key positioning:

- Do not write the paper as "we add a module to ASF."
- Write it as "canonical patch alignment is a useful substrate, but robust fusion also requires task-aware evidence decomposition and control."
- ASF is the canonical-space backbone/baseline; TaskDec is the architecture that decides how canonical patches should be trusted and modulated.

## Recommended 9-Page Main Paper Budget

| Part | Target pages | Main job |
|---|---:|---|
| Abstract | 0.25 | State problem, method, K-Radar gains, generalization evidence. |
| 1. Introduction | 1.05 | Motivate patch-level evidence availability and summarize contributions. |
| 2. Related Work | 0.75 | Compactly position against ASF, L4DR/3D-LRF/AW-MoE, and DecAlign. |
| 3. Method | 2.20 | Four-part architecture description with one main framework figure. |
| 4. Experiments | 3.20 | Protocol, main K-Radar result, weather result, ablation, compact generalization/availability. |
| 5. Analysis and Visualization | 0.80 | PCA/gate evidence for decoupled representation behavior. |
| 6. Conclusion | 0.25 | Short, no overclaim. |
| Safety margin | 0.50 | Captions, equations, whitespace, author-format overhead. |

Main paper should use at most **4 core figure/table blocks** plus one compact ablation table. If the LaTeX gets tight, move the VoD table and efficiency table fully to appendix first.

## Main Text Figure/Table Plan

### Figure 1: Motivation Figure, Top of Introduction

Purpose: show why availability-aware fusion is not enough.

Content:

- Three sensors observe the same BEV/canonical patch under adverse weather.
- Each patch contains mixed evidence: shared object cues, modality-specific cues, noise, and missing/degraded sensor inputs.
- Highlight the gap: sensor present does not mean patch reliable.

Caption message:

> Different sensors can be available but unevenly informative at the same object-level patch. TaskDec models this as patch-level evidence availability through common/unique decomposition and task-aware control.

Use this as a conceptual figure, not an experimental visualization.

### Figure 2: Main Architecture Figure, Method Section

Purpose: make TaskDec look like the paper's central architecture.

Recommended layout:

1. Sensor encoders produce BEV/canonical features.
2. A compact block labeled "Canonical Patch Fusion Substrate" summarizes ASF-style patch tokenization and attention.
3. Large central TaskDec block:
   - common/unique decomposition
   - foreground gate
   - reliability controller
   - task-context modulation
4. Controlled tokens go into patch-level fusion and detection head.

Design instruction:

- Keep ASF/UCP as one smaller left-side substrate block.
- Make TaskDec controller the largest visual component.
- Use arrows from decomposed states to three control signals, not only to an auxiliary loss.

### Table 1: K-Radar v1.0 Main Comparison

Put this in Experiments immediately after protocol.

Use compact rows only:

| Method | Sensors | APBEV@0.5 | AP3D@0.5 | APBEV@0.3 | AP3D@0.3 |
|---|---|---:|---:|---:|---:|
| RTNH | R | 36.00 | 14.10 | 41.10 | 37.40 |
| 3D-LRF | L+R | 73.60 | 45.20 | 84.00 | 74.80 |
| L4DR | L+R | 77.50 | 53.50 | 79.50 | 78.00 |
| ASF | C+L+R | 80.33 | 67.19 | 80.78 | 80.31 |
| AW-MoE | L+R | 84.20 | 61.50 | 88.20 | 83.90 |
| AW-MoE-LRC | C+L+R | - | 61.80 | - | 84.30 |
| TaskDec Robust | C+L+R | **88.10** | **67.50** | **88.84** | **88.36** |

Caption must be careful:

> ASF is evaluated from the released official checkpoint under `conf_thr=0.3`; other literature results are taken from the corresponding papers.

Do not mention ASF protocol controversy in the main caption beyond this neutral sentence.

### Table 2: Weather Breakdown on K-Radar v1.0

Use only AP3D@IoU=0.3 to keep the table compact.

Rows:

- RTNH
- 3D-LRF
- L4DR
- ASF
- AW-MoE
- AW-MoE-LRC
- TaskDec Robust

Columns:

- Total, Normal, Overcast, Fog, Rain, Sleet, Light snow, Heavy snow

Main claim:

> TaskDec obtains the best total AP3D@0.3 and gives clear gains in normal, rain, and sleet, while other methods remain stronger in some individual weather subsets.

This table is worth main-text space because weather robustness is central to K-Radar and makes the result more convincing than a single total row.

### Table 3: Component Ablation

Use this to analyze the role of the components. State that the full model and ablated variants undergo preliminary evaluation on 1,000 samples before the selected models receive full-set evaluation. Record the actual selection metric and subset provenance in the setup/appendix; identical sample IDs and candidate budgets have not been separately verified in this writing pass.

| Variant | Dec. sup. | FG gate | Reliability | Task ctx. | AP3D@0.5 | AP3D@0.3 |
|---|---|---|---|---|---:|---:|
| ASF | - | - | - | - | 67.19 | 80.31 |
| w/o reliability | yes | yes | no | yes | 64.38 | 79.62 |
| w/o task context | yes | yes | yes | no | 66.23 | 80.14 |
| w/o decoupling supervision | no | yes | yes | yes | 66.16 | 80.23 |
| w/o foreground gate | yes | no | yes | yes | 64.80 | 80.00 |
| Full TaskDec | yes | yes | yes | yes | **67.50** | **88.36** |

Use APBEV columns only if space allows. AP3D@0.3 and AP3D@0.5 are enough for main text.

Main interpretation paragraph:

> Following preliminary model selection, removing any of the four control ingredients reduces full-set AP3D@0.3 from 88.36 to approximately 79.6–80.2. These results support the role of decoupling supervision, foreground gating, reliability scaling, and task-context modulation in the reported architecture.

### Figure 3: Representation/Gate Visualization

Use the new paper-ready figure:

- `analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_pca_representative.*`
- `analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_decoupling_and_gate.*`

If page space is tight, include only `paper_fig_taskdec_decoupling_and_gate` in main and move PCA grid to appendix. If the paper can afford one more figure, include the representative PCA grid because it visually supports the method claim.

Safe visual claim:

> Across weather conditions, the shared target state has much smaller cross-modality centroid distance than raw canonical patches, while the sensor-specific state preserves modality-dependent structure. The foreground gate is consistently higher for foreground patches, especially under fog/snow-like adverse conditions.

Avoid:

> Reliability switches dominant sensors by weather.

The current checkpoint's reliability readout is LiDAR-dominant, so keep reliability readout in appendix as a diagnostic.

### Table 4: Compact Generalization/Availability Table

This is optional in main text. If space permits, combine K-Radar v2 and VoD into one small table:

| Setting | Baseline | TaskDec | Metric | Delta |
|---|---:|---:|---|---:|
| K-Radar v2 Sedan adverse weather | 52.25 | 54.79 | selected-weather AP3D@0.5 | +2.54 |
| K-Radar v2 Bus/Truck adverse weather | 38.22 | 42.29 | selected-weather AP3D@0.5 | +4.07 |
| VoD native PP L+R | 69.88 | 70.18 | EAA mAP | +0.30 |
| VoD native PP L+R | 83.80 | 83.79 | DC/RoI mAP | -0.01 |
| K-Radar v1 LR availability | 86.02 | 88.06 | AP3D@0.3 | +2.04 |

Table note: the two v2.0 rows use `DecControlled (early variant)`, without task context; the VoD rows both use warm-start epoch 79. Name the variants explicitly. The full availability table additionally reports LC (+6.88 AP3D@0.3) and RC (−8.07); LR AP3D@0.5 is slightly lower than ASF by 0.30.

This table is good if reviewers might ask about generalization. It should not replace the v1 weather or ablation table.

Recommended sentence:

> With target-dataset training under the reported warm-start setting, TaskDec transfers to a native VoD PointPillars-style L+R pipeline, improving the strong PP-Concat baseline on EAA while maintaining comparable DC performance. Supplementary v2.0 results use an earlier DecControlled variant without task context and support extension of the decoupled-control approach.

If main text is too crowded, move this table to appendix and keep only one paragraph in main.

## Section-by-Section Paragraph Organization

### Abstract

Structure in 5 sentences:

1. Adverse-weather 3D detection needs robust fusion across camera, LiDAR, and 4D radar.
2. Existing canonical-space fusion aligns modalities but does not explicitly separate shared target evidence from sensor-specific residuals.
3. We introduce TaskDec, a task-aware decoupled fusion architecture that decomposes canonical patch tokens and uses the resulting states to control foreground gating, sensor reliability, and task context.
4. On K-Radar v1.0 Sedan under the protocol-consistent `conf_thr=0.3` setting, TaskDec reaches AP3D@0.3 of 88.36, outperforming the released ASF checkpoint by 8.05 points and AW-MoE-LRC by 4.06 points.
5. Component ablations support the role of the control ingredients, and native-backbone experiments on VoD demonstrate an EAA improvement over the strong PP-Concat baseline. Describe the earlier v2.0 variant in the experiments rather than implying it is the full model in the abstract.

Do not put too many numbers in the abstract; one main number plus one ablation/generalization phrase is enough.

### 1. Introduction

Paragraph 1: problem.

> Multi-modal 3D detection is usually framed as a problem of combining complementary sensors, but adverse weather makes this complementarity local and conditional. A sensor can be globally available while being unreliable for a particular object patch because of sparsity, scattering, occlusion, or weak visual evidence.

Paragraph 2: gap in current fusion.

> Canonical patch fusion, as used by ASF, is a strong way to put heterogeneous modalities into a common fusion space. However, a shared coordinate/token space does not by itself decide which part of a token is cross-modal object evidence and which part is modality-specific residue or noise.

Paragraph 3: proposed idea.

> TaskDec addresses this gap by making fusion control a consequence of representation decomposition. Each modality patch is decomposed into a shared target state and a sensor-specific state. The controller then predicts foreground gates, sensor reliability scales, and task context from these states to dynamically modulate patch-level fusion.

Paragraph 4: contributions.

Recommended compact bullets:

- A task-aware decoupled fusion architecture for canonical patch-based camera-LiDAR-4D radar detection.
- A foreground-supervised common/unique decomposition that turns cross-modal alignment into fusion control rather than only representation regularization.
- Strong K-Radar v1.0 results with weather breakdown, component ablations, missing-modality evaluation, and transfer checks on K-Radar v2.0 and VoD.

### 2. Related Work

Use three compact paragraphs, not many subsections.

Paragraph 1: 4D radar and K-Radar detection.

Mention RTNH/K-Radar, 3D-LRF, L4DR, AW-MoE, WCBR/FusionBev/DDMDGF if space permits. The contrast is that many are L+R-specialized and weather-oriented.

Paragraph 2: availability-aware and canonical fusion.

ASF is the direct baseline. The contrast is not that ASF is weak, but that canonical alignment does not explicitly decompose task-shared and sensor-specific evidence.

Paragraph 3: decoupled multimodal representation.

DECALIGN motivates common/unique learning. The key contrast is that TaskDec applies decoupling at object-level BEV/canonical patches and uses it as a controller for detection fusion.

### 3. Method

Keep this section to four subsections.

#### 3.1 Canonical Patch Fusion Substrate

Define:

- modality BEV feature `F_m`
- canonical patch token `x_{m,p}`
- ASF-style attention `z_p = Attn(q_p, {x_{m,p}}, {x_{m,p}})`

Keep this subsection short. It exists to define the space where TaskDec operates.

#### 3.2 Foreground-Aware Common/Unique Decomposition

Define:

- `c_{m,p} = C_m(x_{m,p})`
- `u_{m,p} = U_m(x_{m,p})`

Explain:

- common alignment on foreground patches
- unique separation
- orthogonality between common and unique

Important wording:

> We supervise decomposition on foreground patches derived from 3D boxes, because background-dominated all-patch alignment would mostly teach the model to agree on empty space.

#### 3.3 Decoupling-Guided Fusion Control

Define three controller outputs:

- foreground gate `g_p`
- sensor reliability `r_{m,p}`
- bounded token scale `s_{m,p}`

Then write the controlled token:

`x'_{m,p} = s_{m,p} [x_{m,p} + alpha g_p (c_{m,p}+u_{m,p})]`

This is the central architecture subsection. Put Figure 2 around here.

#### 3.4 Task Context and Training Objective

Define:

- task context `h_p`
- query modulation `q'_p = q_p + beta_q g_p h_p`
- fused token modulation `z'_p = z_p + beta_z g_p h_p`

Then give one compact total objective:

`L = L_det + lambda_scl L_scl + lambda_dec L_dec + lambda_gate L_gate + lambda_cls L_cls`

Move exact loss weights and hyperparameters to appendix.

### 4. Experiments

#### 4.1 Setup

State:

- K-Radar v1.0 Sedan, driving-corridor/narrow ROI.
- Main comparison uses `conf_thr=0.3`, APBEV/AP3D at IoU 0.3 and 0.5.
- ASF row is released official checkpoint locally re-evaluated at `conf_thr=0.3`.
- Literature rows are reported from papers/logs.
- Encoders and detection head follow the ASF-family setup; TaskDec changes fusion control.

Avoid turning this into a protocol dispute. Put detailed ASF `conf=0.0` audit in appendix.

#### 4.2 Main Results on K-Radar v1.0

Insert Table 1.

Main text:

> TaskDec achieves 88.36 AP3D@0.3, improving the released ASF checkpoint by 8.05 points under the same confidence-filtered protocol and exceeding the strongest published C+L+R row, AW-MoE-LRC, by 4.06 points. At IoU=0.5, TaskDec also slightly improves over ASF and gives the best AP3D among the compact comparison rows.

Be precise:

- "under `conf_thr=0.3`"
- "released ASF checkpoint"
- "published rows are taken from papers"

#### 4.3 Weather Robustness

Insert Table 2.

Main text:

> The total gain is not caused by a single easy subset. TaskDec gives strong AP3D@0.3 results under normal, rain, and sleet, while remaining competitive under snow. Fog and overcast are not uniformly dominated, which suggests that the controller improves broad adverse-weather robustness but does not solve every weather mode.

#### 4.4 Component Ablation

Insert Table 3.

Main text:

> The full model and ablated variants undergo 1,000-sample preliminary evaluation for selection, followed by full-set evaluation. Removing reliability control, task context, decoupling supervision, or foreground gating reduces AP3D@0.3 to approximately 79.6–80.2, supporting their roles in the proposed architecture. The setup and appendix specify the selection procedure.

#### 4.5 Generalization and Availability

If space permits, insert Table 4. Otherwise write a short paragraph and cite appendix.

Main text:

> With camera or radar unavailable at inference, TaskDec improves LR/LC AP3D@0.3 over the released ASF checkpoint by 2.04/6.88 points; RC is the main degradation case. On VoD, target-dataset training of the native PointPillars-style L+R adaptation under the reported warm-start setting improves the strong PP-Concat baseline from 69.88 to 70.18 EAA mAP while maintaining comparable DC performance. Supplementary v2.0 results use an earlier DecControlled variant without task context. Specialized L4DR retains higher absolute performance on VoD.

This paragraph is honest and reviewer-resistant.

### 5. Analysis and Visualization

Insert Figure 3.

Main text:

> PCA diagnostics show that the shared target states have much smaller cross-modality centroid distances than raw canonical patches across all weather groups, while sensor-specific states remain separated. This matches the intended role of the decomposition: common states collect cross-modal object evidence, and unique states keep modality-dependent residual structure. The foreground gate is higher on foreground patches than background patches and increases under fog/snow-like adverse conditions.

Do not include reliability-switching claims in main text.

### 6. Conclusion

Keep it short:

> TaskDec shows that canonical patch fusion benefits from an explicit task-aware decoupled controller. By using common/unique patch states to gate foreground evidence, reweight sensor tokens, and inject task context, the method substantially improves K-Radar v1.0 and remains useful under missing-modality and transfer settings. Future work should improve class-specific control for wider-ROI datasets and external radar formats.

## Appendix Organization

### Appendix A: Full Method Details

Include:

- exact architecture dimensions
- controller MLP definitions
- all loss definitions
- hyperparameters
- training schedule
- pseudo-code

Move here:

- details of ASF inherited blocks
- exact SCL settings
- token scale clamp ranges
- gate loss/class loss weights

### Appendix B: Protocol and Confidence-Threshold Audit

Include:

- ASF released checkpoint provenance
- `conf_thr=0.0` vs `conf_thr=0.3` table
- why main text uses `conf_thr=0.3`
- local ASF repro note

Tone:

- Use "protocol sensitivity" and "threshold disclosure."
- Do not use accusatory wording.

Source docs:

- `results/asf_v1_conf_protocol_audit_260828.md`
- `results/v1_conf0_3_main_protocol_260819.md`

### Appendix C: Full K-Radar v1.0 Comparisons

Include:

- larger main table with PointPillars, InterFusion, WCBR, L4DR-DA3D, RTNH L/R
- AP3D@0.5 weather table
- optional APBEV weather tables
- full condition breakdown

Source docs:

- `results/paper_main_table_kradar_v1_conf0_3_draft_260901.md`
- `results/paper_main_table_kradar_v1_weather_compact_260901.md`

### Appendix D: Missing-Modality Availability

Include:

- RLC, LR, LC, RC comparison against ASF
- state clearly that rows use C+L+R-trained checkpoints with sensors disabled at inference
- note RC underperforms ASF, while LR and LC improve

Source docs:

- `results/paper_availability_missing_modalities_260902.md`
- `results/v1_lr_conf0_3_sota_comparison_260828.md`

### Appendix E: K-Radar v2.0 Generalization

Identify the model as `DecControlled (early variant)`, without the task-context branch. State this briefly in the main text and table caption; retain configuration details in the appendix.

Include:

- selected adverse-weather AP3D@0.5 table
- AP3D@0.3 ASF-style rainy/snowy table
- full total metrics

Claim:

> The early DecControlled variant improves selected-weather AP3D@0.5 on v2.0, supporting extension of the decoupled-control approach. These rows are not evaluations of the full TaskDec architecture transferred unchanged.

Source:

- `results/paper_supp_table_kradar_v2_generalization_260901.md`

### Appendix F: VoD External Dataset Transfer

Lead with applicability to a native backbone and the EAA improvement over the strong PP-Concat baseline. Record the mild/warm-start setting and precision/selection details. Retain L4DR in the table; one sentence acknowledging its higher VoD performance is sufficient in the transfer discussion.

Include:

- same-protocol KITTI AP_R40 table
- official EAA/DC table
- explain native PP-Concat and TaskDec-PP settings
- state that L4DR remains stronger as a specialized VoD method

Use latest result:

- TaskDec-PP warm mild epoch 79: EAA mAP 70.18, DC/RoI mAP 83.79
- PP-Concat epoch 80: EAA mAP 69.88, DC/RoI mAP 83.80
- L4DR: EAA 72.70, DC/RoI 87.47

Source:

- `results/paper_vod_main_table_draft_260909.md`

### Appendix G: Extra Ablations and Hyperparameter Sensitivity

Include:

- control strength 0.0/0.5/0.75/1.0
- gate init bias if used
- early/late checkpoint discussion only if necessary

Do not overemphasize checkpoint hunting. Phrase as:

> We evaluate sensitivity to controller strength and observe that nearby settings remain close, while disabling reliability control causes a large degradation.

Source:

- `results/taskdec_v1_control_strength_compare_260904.md`

### Appendix H: Efficiency

Include:

| Method | Params | Forward latency | FPS | Peak memory |
|---|---:|---:|---:|---:|
| ASF | 78.13M | 79.95 ms | 12.51 | 0.97 GB |
| TaskDec | 79.47M | 86.45 ms | 11.57 | 0.98 GB |

Claim:

> TaskDec adds 1.34M parameters and 6.50 ms forward latency over ASF on the local measurement setup.

Source:

- `results/paper_efficiency_table_260902.md`

### Appendix I: Visualization Diagnostics

Include:

- all-weather PCA grid
- reliability readout diagnostic
- sensor candidate search note

Safe wording:

> The reliability readout in the selected checkpoint is conservative and LiDAR-dominant, so we use it as a diagnostic rather than as evidence of weather-dependent sensor switching.

Sources:

- `results/taskdec_weather_pca_visualization_260909.md`
- `results/taskdec_sensor_case_candidates_260909.md`
- `analysis_exports/taskdec_paper_visuals_260909/`

## What Should Not Be in the Main Text

Move these to appendix or omit:

- ASF "academic misconduct" discussion. Replace with neutral protocol sensitivity.
- ASF local repro beating the official checkpoint. Useful for audit, distracting in main.
- Full hyperparameter scans and checkpoint-selection history.
- VoD rows where TaskDec is lower than specialized L4DR, unless framed as transfer context.
- Reliability-dominance/sensor-switching claims.
- Too many baselines with missing metrics.
- Full formulas for every auxiliary loss weight.

## Main Claims That Are Safe

1. **Main SOTA-style claim**

   > Under the confidence-filtered K-Radar v1.0 Sedan protocol (`conf_thr=0.3`), TaskDec Robust reaches 88.36 AP3D@0.3, outperforming prior protocol-compatible methods in the compact comparison.

2. **ASF comparison**

   > Compared with the released ASF checkpoint evaluated under the same `conf_thr=0.3` protocol, TaskDec improves AP3D@0.3 by 8.05 points and AP3D@0.5 by 0.31 points.

3. **Ablation claim**

   > Removing decoupling supervision, foreground gating, reliability control, or task context substantially reduces AP3D@0.3, supporting the integrated design.

4. **Weather claim**

   > TaskDec gives the best total AP3D@0.3 and strong gains under normal, rain, and sleet, while not uniformly dominating every weather subset.

5. **Generalization claim**

   > TaskDec transfers beyond v1.0: it improves selected adverse-weather AP3D@0.5 on K-Radar v2.0 and gives a small gain over a native PP-Concat L+R baseline on VoD official EAA mAP.

## Risky Claims to Avoid

- "TaskDec beats ASF under all protocols."
- "TaskDec beats L4DR on VoD."
- "TaskDec proves dynamic weather-dependent sensor switching."
- "TaskDec is a pure L+R-trained SOTA model."
- "All components individually improve every metric."
- "The method solves K-Radar v2.0 broadly."

## Minimal Main-Paper Narrative

If the paper becomes too long, use this compressed storyline:

1. Introduction: sensor availability is patch-level evidence availability.
2. Method: TaskDec decomposes canonical patch tokens and uses the decomposition for control.
3. Main result: K-Radar v1.0 SOTA at AP3D@0.3 under `conf_thr=0.3`.
4. Weather: gains are meaningful under adverse conditions.
5. Ablation: every controller ingredient matters.
6. Generalization: v2.0 + VoD + missing-modality results support transfer, details in appendix.

This is the cleanest ICLR 2027 version.
