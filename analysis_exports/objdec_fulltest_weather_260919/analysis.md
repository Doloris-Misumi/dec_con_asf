# ObjDec full-test weather representation analysis

- Complete frames: 10065; valid foreground frames: 10065.
- Full v1 test split; all 10,065 frames processed.
- Each frame mean uses ALL GT-foreground patches, with the original foreground mask and configured margin.
- Main weather means give equal weight to each valid frame; empty-foreground frames are counted and excluded.
- PCA here is fitted to frame-mean vectors, balancing weather groups and modalities; one fixed basis per representation.
- This PCA describes between-frame-mean variation, unlike the existing patch-scatter PCA. Do not directly compare axes between figures.
- Plot points may be subsampled for readability; large centers and tables use all valid frames.
- Sequence-equal and patch-equal cosine summaries are provided as sensitivity checks, not significance tests.
- Weather is observational and confounded with sequence/scene; neither causality nor semantic disentanglement is established by PCA alone.

| Weather | Valid frames | Sequences | Input cosine | Common cosine | Unique cosine |
|---|---:|---:|---:|---:|---:|
| normal | 4309 | 17 | 0.0030 | 0.9553 | 0.4462 |
| overcast | 383 | 2 | 0.0055 | 0.9590 | 0.4941 |
| fog | 1049 | 6 | 0.0012 | 0.9514 | 0.5281 |
| rain | 1317 | 8 | -0.0008 | 0.9528 | 0.4711 |
| sleet | 1106 | 7 | 0.0055 | 0.9566 | 0.5494 |
| lightsnow | 803 | 4 | -0.0063 | 0.9558 | 0.5340 |
| heavysnow | 1098 | 7 | -0.0016 | 0.9536 | 0.5368 |
