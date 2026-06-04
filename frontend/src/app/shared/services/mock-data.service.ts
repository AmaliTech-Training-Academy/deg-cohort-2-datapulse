import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { Alert, AdminUserRow, Project, QualityReport, QualityThresholds, ValidationRule } from '../models/dashboard.models';
import { MOCK_PROJECTS, MOCK_REPORTS } from '../mock/mock-projects';
import { MOCK_ALERTS } from '../mock/mock-alerts';
import { MOCK_USERS } from '../mock/mock-users';
import { DEFAULT_THRESHOLDS } from '../mock/mock-settings';
import { MOCK_DATASET_COLUMNS, MOCK_VALIDATION_RULES } from '../mock/mock-validation-rules';

@Injectable({ providedIn: 'root' })
export class MockDataService {
  getMyProjects(userId: string): Observable<Project[]> {
    return of(MOCK_PROJECTS.filter((p) => p.ownerId === userId)).pipe(delay(300));
  }

  getAllProjects(): Observable<Project[]> {
    return of(MOCK_PROJECTS).pipe(delay(300));
  }

  getProjectById(id: string): Observable<Project | undefined> {
    return of(MOCK_PROJECTS.find((p) => p.id === id)).pipe(delay(200));
  }

  getQualityReport(datasetId: string): Observable<QualityReport | undefined> {
    return of(MOCK_REPORTS[datasetId]).pipe(delay(200));
  }

  getAlerts(): Observable<Alert[]> {
    return of(MOCK_ALERTS).pipe(delay(300));
  }

  getAllUsers(): Observable<AdminUserRow[]> {
    return of(MOCK_USERS).pipe(delay(300));
  }

  getSettings(): Observable<QualityThresholds> {
    return of({ ...DEFAULT_THRESHOLDS }).pipe(delay(200));
  }

  saveSettings(settings: QualityThresholds): Observable<void> {
    Object.assign(DEFAULT_THRESHOLDS, settings);
    return of(undefined).pipe(delay(400));
  }

  getValidationRules(datasetId: string): Observable<ValidationRule[]> {
    return of([...(MOCK_VALIDATION_RULES[datasetId] ?? [])]).pipe(delay(100));
  }

  getDatasetColumns(datasetId: string): Observable<string[]> {
    return of(MOCK_DATASET_COLUMNS[datasetId] ?? []).pipe(delay(100));
  }

  getPlatformStats() {
    const projects = MOCK_PROJECTS;
    const healthy = projects.filter((p) => p.status === 'healthy').length;
    const warning = projects.filter((p) => p.status === 'warning').length;
    const failing = projects.filter((p) => p.status === 'failing').length;
    return of({
      totalProjects: 42,
      projectDelta: 3,
      activeUsers: 128,
      adminCount: 14,
      checksToday: 1204,
      checksDatasetsCount: 38,
      failingDatasets: 9,
      healthyCount: healthy + 28,
      warningCount: warning + 4,
      failingCount: failing + 3,
      storageUsedPercent: 68,
      storageUsedTB: 6.8,
      storageTotalTB: 10,
      rulesRunToday: 1204,
      rulesTotalToday: 1470,
      rulesRunPercent: 82,
      errorRate: 4,
    }).pipe(delay(200));
  }
}
