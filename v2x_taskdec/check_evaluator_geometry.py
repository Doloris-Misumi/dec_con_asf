"""Independent OpenCV polygon reference; no model predictions or protocol tuning."""
import json
from pathlib import Path
import cv2
import numpy as np
from .evaluation.rotate_iou import rotate_iou_gpu_eval


def main():
    rng = np.random.RandomState(260916)
    boxes = np.column_stack([rng.uniform(-50, 100, (100, 2)),
                             rng.uniform(.3, 8, (100, 2)), rng.uniform(-np.pi, np.pi, 100)])
    queries = boxes.copy()
    queries[50:, :2] += rng.uniform(-2, 2, (50, 2))
    queries[50:, 4] += rng.uniform(-.5, .5, 50)
    # OpenCV uses counterclockwise algebraic rotation; the official camera
    # evaluator uses clockwise x-z rotation.
    def corners(b):
        return cv2.boxPoints(((float(b[0]), float(b[1])), (float(b[2]), float(b[3])),
                              float(-b[4] * 180 / np.pi)))
    reference = np.zeros((100, 100))
    for i, a in enumerate(boxes):
        for j, b in enumerate(queries):
            reference[i, j] = cv2.intersectConvexConvex(corners(a), corners(b))[0]
    intersection = rotate_iou_gpu_eval(boxes, queries, 2)
    max_error = float(np.abs(reference - intersection).max())
    assert max_error < .002, max_error
    self_iou = np.diag(rotate_iou_gpu_eval(boxes, boxes))
    assert np.allclose(self_iou, 1, atol=2e-5), self_iou
    # Symmetry, directed area normalization and exact disjointness.
    assert np.allclose(intersection, rotate_iou_gpu_eval(queries, boxes, 2).T, atol=2e-5)
    simple = np.array([[0, 0, 4, 2, 0], [1, 0, 4, 2, 0], [100, 0, 4, 2, 0]], float)
    np.testing.assert_allclose(rotate_iou_gpu_eval(simple, simple),
                               [[1, .6, 0], [.6, 1, 0], [0, 0, 1]], atol=1e-6)
    result = dict(status='passed',opencv_version=cv2.__version__,pairs=10000,
                  max_intersection_error_m2=max_error,self_iou_max_error=float(abs(self_iou-1).max()))
    path=Path(__file__).resolve().parents[1]/'analysis_exports/v2x_taskdec_260916/evaluator_geometry_check.json'
    path.write_text(json.dumps(result,indent=2));print(result)


if __name__ == '__main__':
    main()
