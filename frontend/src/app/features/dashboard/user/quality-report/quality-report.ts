import { Component, computed, inject, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Store } from '@ngrx/store';
import { QualityReport, FindingCheck } from '../../../../shared/models/dashboard.models';
import { ScoreRingComponent } from '../../../../shared/ui/score-ring/score-ring';
import * as ReportDetailActions from '../../store/report-detail/report-detail.actions';
import {
  selectReportDetail,
  selectReportDetailLoading,
} from '../../store/report-detail/report-detail.selectors';

function formatRuleType(ruleType: string): string {
  switch (ruleType) {
    case 'null_check':
      return 'Null check';
    case 'type_check':
      return 'Type check';
    case 'range_check':
      return 'Range check';
    case 'uniqueness_check':
      return 'Uniqueness check';
    default:
      return ruleType.replace(/_/g, ' ');
  }
}

@Component({
  selector: 'app-quality-report',
  standalone: true,
  imports: [RouterLink, ScoreRingComponent],
  templateUrl: './quality-report.html',
  styleUrl: './quality-report.css',
})
export class QualityReportComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly store = inject(Store);

  private projectId = '';

  private readonly reportDetailData = this.store.selectSignal(selectReportDetail);
  protected readonly loading = this.store.selectSignal(selectReportDetailLoading);

  // Map ReportDetail from the store to the QualityReport shape the template expects
  protected readonly report = computed((): QualityReport | undefined => {
    const detail = this.reportDetailData();
    if (!detail) return undefined;

    const findings: FindingCheck[] = detail.findings.map((f) => ({
      id: f.id,
      name: `${formatRuleType(f.ruleType)} on ${f.columnName}`,
      // Map 'uniqueness_check' → 'uniqueness' to match existing icon switch case
      type: f.ruleType === 'uniqueness_check' ? 'uniqueness' : f.ruleType,
      description:
        f.rowsFailed > 0
          ? `${f.rowsFailed.toLocaleString()} of ${f.rowsChecked.toLocaleString()} rows failed (${f.failurePercentage.toFixed(1)}%)`
          : `All ${f.rowsChecked.toLocaleString()} rows passed`,
      status: f.rowsFailed > 0 ? ('failed' as const) : ('passed' as const),
      failingRows: f.rowsFailed > 0 ? f.rowsFailed : undefined,
    }));

    return {
      datasetId: detail.datasetId,
      datasetName: detail.datasetFileTitle || detail.datasetFileName,
      projectId: this.projectId,
      projectName: detail.datasetFileTitle || detail.datasetFileName,
      version: `v${detail.datasetFileVersion}`,
      overallScore: detail.overallScore ?? 0,
      categoryScores: {
        nullChecks: detail.categoryScores.nullChecks ?? 0,
        typeChecks: detail.categoryScores.typeChecks ?? 0,
        rangeChecks: detail.categoryScores.rangeChecks ?? 0,
        uniqueness: detail.categoryScores.uniqueness ?? 0,
      },
      findings,
    };
  });

  ngOnInit(): void {
    this.projectId = this.route.snapshot.paramMap.get('id') ?? '';
    const reportId = this.route.snapshot.paramMap.get('reportId') ?? '';
    this.store.dispatch(ReportDetailActions.clearReportDetail());
    this.store.dispatch(ReportDetailActions.loadReportDetail({ reportId }));
  }

  ngOnDestroy(): void {
    this.store.dispatch(ReportDetailActions.clearReportDetail());
  }

  protected findingIcon(status: string, type: string): string {
    if (status === 'passed') {
      return 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z';
    }
    switch (type) {
      case 'uniqueness':
        return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z';
      default:
        return 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
    }
  }

  protected findingIconColor(status: string): string {
    return status === 'passed' ? 'var(--color-success)' : 'var(--color-warning)';
  }
}
