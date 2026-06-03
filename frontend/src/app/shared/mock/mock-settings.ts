import { QualityThresholds } from '../models/dashboard.models';

export const DEFAULT_THRESHOLDS: QualityThresholds = {
  healthyMin: 85,
  warningMin: 70,
  autoPauseAfterFailures: 3,
  slowRunThresholdSeconds: 180,
};
