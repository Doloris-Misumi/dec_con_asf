# ObjDec full-test weather representation analysis

- Complete frames: 7; valid foreground frames: 7.
- Smoke only.
- Each frame mean uses ALL GT-foreground patches, with the original foreground mask and configured margin.
- Main weather means give equal weight to each valid frame; empty-foreground frames are counted and excluded.
- PCA here is fitted to frame-mean vectors, balancing weather groups and modalities; one fixed basis per representation.
- This PCA describes between-frame-mean variation, unlike the existing patch-scatter PCA. Do not directly compare axes between figures.
- Plot points may be subsampled for readability; large centers and tables use all valid frames.
- Sequence-equal and patch-equal cosine summaries are provided as sensitivity checks, not significance tests.
- Weather is observational and confounded with sequence/scene; neither causality nor semantic disentanglement is established by PCA alone.

| Weather | Valid frames | Sequences | Input cosine | Common cosine | Unique cosine |
|---|---:|---:|---:|---:|---:|
| normal | 1 | 1 | 0.0036 | 0.9541 | 0.4801 |
| overcast | 1 | 1 | 0.0078 | 0.9549 | 0.4629 |
| fog | 1 | 1 | 0.0011 | 0.9573 | 0.5689 |
| rain | 1 | 1 | -0.0130 | 0.9393 | 0.3014 |
| sleet | 1 | 1 | 0.0107 | 0.9664 | 0.3159 |
| lightsnow | 1 | 1 | 0.0046 | 0.9571 | 0.5063 |
| heavysnow | 1 | 1 | 0.0272 | 0.9352 | 0.4617 |
