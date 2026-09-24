# TaskDec Weather PCA Analysis

Export: weather-balanced foreground/background patch sample.

## PCA Explained Variance

| Feature | PC1 | PC2 |
|---|---:|---:|
| raw | 59.26% | 9.70% |
| common | 71.87% | 13.78% |
| unique | 70.38% | 12.53% |

## Foreground Gate By Weather

| Weather | Gate fg | Gate bg | Delta |
|---|---:|---:|---:|
| normal | 0.1997 | 0.0700 | 0.1297 |
| overcast | 0.1913 | 0.0631 | 0.1282 |
| fog | 0.2470 | 0.0547 | 0.1923 |
| rain | 0.1974 | 0.0608 | 0.1366 |
| sleet | 0.2194 | 0.0584 | 0.1609 |
| lightsnow | 0.2238 | 0.0578 | 0.1660 |
| heavysnow | 0.2162 | 0.0555 | 0.1607 |

## Mean Modality-Centroid Distance

| Weather | Raw | Common | Unique |
|---|---:|---:|---:|
| normal | 14.48 | 3.32 | 20.44 |
| overcast | 14.66 | 3.37 | 19.30 |
| fog | 14.47 | 3.20 | 17.14 |
| rain | 14.50 | 3.55 | 19.27 |
| sleet | 14.64 | 2.54 | 15.29 |
| lightsnow | 14.74 | 3.26 | 16.97 |
| heavysnow | 14.39 | 2.56 | 16.51 |

## Suggested Figure Choices

- Largest common-state sensor spread: `rain` (3.55).
- Largest unique-state sensor spread: `normal` (20.44).
- In this checkpoint, the learned reliability is strongly LiDAR-dominant across all weather groups, so PCA/centroid-distance plots are more informative than reliability bars for showing sensor-specific structure.