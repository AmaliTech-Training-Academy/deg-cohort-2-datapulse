import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { ApiDashboardResponse, ApiDataset } from '../models/project.model';
import { ApiReportsListResponse } from '../models/report.model';
import { ApiTrendPoint } from '../models/trend.model';
import { ApiReportDetail } from '../models/report-detail.model';
import { DatasetUploadResponse } from '../models/dataset-upload.model';
import { RulesBatchRequest, RulesBatchResponse } from '../models/rules-batch.model';
import { RunCheckResponse } from '../models/run-check.model';
import {
  ApiRulesListResponse,
  ApiValidationRule,
  CreateRuleRequest,
} from '../models/validation-rule.model';
import {
  AdminDatasetsParams,
  ApiAdminDatasetsResponse,
} from '../models/admin-dataset.model';
import { ApiAdminUsersResponse } from '../models/admin-user.model';

@Injectable({ providedIn: 'root' })
export class DashboardApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/v1`;

  getProjects(): Observable<ApiDashboardResponse> {
    return this.http.get<ApiDashboardResponse>(`${this.base}/dashboard/`);
  }

  getProject(datasetId: string): Observable<ApiDataset> {
    return this.http.get<ApiDataset>(`${this.base}/datasets/${datasetId}/`);
  }

  getReports(datasetId: string): Observable<ApiReportsListResponse> {
    return this.http.get<ApiReportsListResponse>(`${this.base}/datasets/${datasetId}/reports/`);
  }

  getTrends(datasetId: string): Observable<ApiTrendPoint[]> {
    return this.http.get<ApiTrendPoint[]>(`${this.base}/datasets/${datasetId}/trends/`);
  }

  getReportDetail(reportId: string): Observable<ApiReportDetail> {
    return this.http.get<ApiReportDetail>(`${this.base}/reports/${reportId}/`);
  }

  uploadDataset(formData: FormData): Observable<DatasetUploadResponse> {
    return this.http.post<DatasetUploadResponse>(`${this.base}/datasets/upload/`, formData);
  }

  saveRulesBatch(datasetId: string, payload: RulesBatchRequest): Observable<RulesBatchResponse> {
    return this.http.post<RulesBatchResponse>(
      `${this.base}/datasets/${datasetId}/rules/batch/`,
      payload,
    );
  }

  runChecks(datasetId: string): Observable<RunCheckResponse> {
    return this.http.post<RunCheckResponse>(`${this.base}/datasets/${datasetId}/run-check/`, null);
  }

  getRules(datasetId: string): Observable<ApiRulesListResponse> {
    return this.http.get<ApiRulesListResponse>(`${this.base}/datasets/${datasetId}/rules/`);
  }

  createRule(datasetId: string, request: CreateRuleRequest): Observable<ApiValidationRule> {
    return this.http.post<ApiValidationRule>(`${this.base}/datasets/${datasetId}/rules/`, request);
  }

  deleteRule(ruleId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/rules/${ruleId}/`);
  }

  deleteDataset(datasetId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/datasets/${datasetId}/`);
  }

  uploadNewVersion(datasetId: string, file: File): Observable<void> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.patch<void>(`${this.base}/datasets/${datasetId}/file/`, formData);
  }

  getAdminDatasets(params: AdminDatasetsParams = {}): Observable<ApiAdminDatasetsResponse> {
    let p = new HttpParams();
    if (params.search) p = p.set('search', params.search);
    if (params.file_type) p = p.set('file_type', params.file_type);
    if (params.created_from) p = p.set('created_from', params.created_from);
    if (params.created_to) p = p.set('created_to', params.created_to);
    if (params.page) p = p.set('page', params.page);
    if (params.page_size) p = p.set('page_size', params.page_size);
    return this.http.get<ApiAdminDatasetsResponse>(`${this.base}/datasets/`, { params: p });
  }

  getAdminUsers(params: { page?: number; page_size?: number } = {}): Observable<ApiAdminUsersResponse> {
    let p = new HttpParams();
    if (params.page) p = p.set('page', params.page);
    if (params.page_size) p = p.set('page_size', params.page_size);
    return this.http.get<ApiAdminUsersResponse>(`${this.base}/auth/users/`, { params: p });
  }
}
