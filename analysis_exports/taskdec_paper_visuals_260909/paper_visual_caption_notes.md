# TaskDec Paper Visualization Notes

Recommended main-text figure:

- `paper_fig_taskdec_pca_representative.*`: compact PCA evidence that the shared target state aligns modalities while the sensor-specific state preserves modality-dependent variation.
- `paper_fig_taskdec_decoupling_and_gate.*`: quantitative companion figure for modality-centroid distance and foreground gate response.

Recommended appendix figure:

- `paper_fig_taskdec_pca_all_weather_appendix.*`: all-weather PCA grid.
- `paper_fig_taskdec_reliability_readout.*`: auxiliary controller readout. The reliability head is LiDAR-dominant in this checkpoint, so use this as a diagnostic rather than evidence of sensor switching.

Safe wording:

> The learned controller produces a compact modality-shared state and a separated modality-specific state across weather conditions. Foreground gates increase on task-relevant patches, while the reliability readout remains conservative and LiDAR-dominant in this checkpoint.
