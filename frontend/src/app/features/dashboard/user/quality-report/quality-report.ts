import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MockDataService } from '../../../../shared/services/mock-data.service';
import { QualityReport } from '../../../../shared/models/dashboard.models';
import { ScoreRingComponent } from '../../../../shared/ui/score-ring/score-ring';

@Component({
  selector: 'app-quality-report',
  standalone: true,
  imports: [RouterLink, ScoreRingComponent],
  templateUrl: './quality-report.html',
  styleUrl: './quality-report.css',
})
export class QualityReportComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly dataService = inject(MockDataService);

  protected readonly report = signal<QualityReport | undefined>(undefined);
  protected readonly loading = signal(true);

  ngOnInit(): void {
    const datasetId = this.route.snapshot.paramMap.get('datasetId') ?? '';
    const projectId = this.route.snapshot.paramMap.get('id') ?? '';
    this.dataService.getQualityReport(datasetId).subscribe((r) => {
      this.report.set(r ?? this.fallbackReport(projectId, datasetId));
      this.loading.set(false);
    });
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

  private fallbackReport(projectId: string, datasetId: string): QualityReport {
    return {
      datasetId,
      datasetName: datasetId,
      projectId,
      projectName: 'Project',
      version: 'v1',
      overallScore: 0,
      categoryScores: { nullChecks: 0, typeChecks: 0, rangeChecks: 0, uniqueness: 0 },
      findings: [],
    };
  }
}
