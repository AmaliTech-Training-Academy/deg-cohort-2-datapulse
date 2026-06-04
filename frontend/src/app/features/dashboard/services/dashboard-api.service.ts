import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { ApiDashboardResponse, ApiDataset } from '../models/project.model';
import { ApiReportsListResponse } from '../models/report.model';
import { ApiTrendPoint } from '../models/trend.model';
import { ApiReportDetail } from '../models/report-detail.model';
import { DatasetUploadResponse } from '../models/dataset-upload.model';
import { RulesBatchRequest, RulesBatchResponse } from '../models/rules-batch.model';
import { RunCheckResponse } from '../models/run-check.model';

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
    return this.http.post<RunCheckResponse>(
      `${this.base}/datasets/${datasetId}/run-check/`,
      null,
    );
  }
}
