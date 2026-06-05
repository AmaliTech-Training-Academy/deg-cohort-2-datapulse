import { UserRole } from '../../features/auth/auth.models';

export type ProjectStatus = 'healthy' | 'warning' | 'failing';

export interface ScoreTrendPoint {
  version: string;
  score: number;
}

export interface Dataset {
  id: string;
  projectId: string;
  name: string;
  version: string;
  rows: number;
  score: number;
  status: ProjectStatus;
  uploadedAt: string;
  activeRules: number;
  failingRows: number;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  ownerId: string;
  ownerName: string;
  status: ProjectStatus;
  datasetCount: number;
  avgScore: number;
  lastRunAt: string;
  activeRulesCount: number;
  iconKey: string;
  datasets: Dataset[];
  scoreTrend: ScoreTrendPoint[];
}

export interface FindingCheck {
  id: string;
  name: string;
  type: string;
  description: string;
  status: 'passed' | 'failed';
  failingRows?: number;
}

export interface QualityReport {
  datasetId: string;
  datasetName: string;
  projectId: string;
  projectName: string;
  version: string;
  overallScore: number;
  categoryScores: {
    nullChecks: number;
    typeChecks: number;
    rangeChecks: number;
    uniqueness: number;
  };
  findings: FindingCheck[];
}

export type AlertSeverity = 'critical' | 'warning' | 'slow' | 'breach' | 'resolved';

export interface Alert {
  id: string;
  severity: AlertSeverity;
  title: string;
  description: string;
  projectName: string;
  assigneeName: string | null;
  isRead: boolean;
  isResolved: boolean;
  createdAt: string;
}

export interface AdminUserRow {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  projectCount: number;
  status: 'active' | 'invited' | 'suspended';
  lastActiveAt: string | null;
}

export interface QualityThresholds {
  healthyMin: number;
  warningMin: number;
  autoPauseAfterFailures: number;
  slowRunThresholdSeconds: number;
}

export interface SuggestedRule {
  id: string;
  name: string;
  type: string;
  description: string;
  column: string;
  enabled: boolean;
  params?: string;
}

export interface DetectedColumn {
  name: string;
  type: 'String' | 'Integer' | 'Date' | 'Datetime' | 'Enum' | 'Float' | 'Boolean';
}

export interface ValidationRule {
  id: string;
  name: string;
  description: string;
  type: 'not_null' | 'type_check' | 'range' | 'unique' | 'format';
  column: string;
  enabled: boolean;
  status: 'passing' | 'failing';
  failingRows?: number;
  deprecated?: boolean;
}
