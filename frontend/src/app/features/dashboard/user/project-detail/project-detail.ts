import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Store } from '@ngrx/store';
import { MockDataService } from '../../../../shared/services/mock-data.service';
import { ValidationRule, ScoreTrendPoint } from '../../../../shared/models/dashboard.models';
import { selectUserRole } from '../../../../features/auth/store/auth.selectors';
import { StatCardComponent } from '../../../../shared/ui/stat-card/stat-card';
import { BadgeComponent } from '../../../../shared/ui/badge/badge';
import { TrendChartComponent } from '../../../../shared/ui/trend-chart/trend-chart';
import { ConfirmationModalComponent } from '../../../../shared/ui/confirmation-modal/confirmation-modal';
import * as ProjectDetailActions from '../../store/project-detail/project-detail.actions';
import * as ReportsActions from '../../store/reports/reports.actions';
import * as TrendsActions from '../../store/trends/trends.actions';
import { selectProjectDetailDataset, selectProjectDetailLoading } from '../../store/project-detail/project-detail.selectors';
import { selectAllReports, selectReportsLoading, selectReportsSummary } from '../../store/reports/reports.selectors';
import { selectTrendsData, selectTrendsLoading } from '../../store/trends/trends.selectors';
import { ProjectStatus } from '../../models/project.model';

interface EditDraft {
  name: string;
  description: string;
  type: ValidationRule['type'];
  column: string;
}

// View model that maps API data into the shape the template expects
interface ReportAsDataset {
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

interface ProjectDetailView {
  id: string;
  name: string;
  datasetCount: number;
  activeRulesCount: number;
  lastRunAt: string;
  avgScore: number;
  status: ProjectStatus;
  datasets: ReportAsDataset[];
  scoreTrend: ScoreTrendPoint[];
}

@Component({
  selector: 'app-project-detail',
  standalone: true,
  imports: [RouterLink, StatCardComponent, BadgeComponent, TrendChartComponent, ConfirmationModalComponent],
  templateUrl: './project-detail.html',
  styleUrl: './project-detail.css',
})
export class ProjectDetailComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly dataService = inject(MockDataService);
  private readonly store = inject(Store);

  protected readonly role = this.store.selectSignal(selectUserRole);
  protected readonly projectsLink = () =>
    this.role() === 'admin' ? '/dashboard/all-projects' : '/dashboard/projects';

  // Store signals
  private readonly datasetFromStore = this.store.selectSignal(selectProjectDetailDataset);
  private readonly projectDetailLoading = this.store.selectSignal(selectProjectDetailLoading);
  private readonly allReports = this.store.selectSignal(selectAllReports);
  private readonly reportsSummary = this.store.selectSignal(selectReportsSummary);
  private readonly trendsData = this.store.selectSignal(selectTrendsData);
  private readonly reportsLoading = this.store.selectSignal(selectReportsLoading);
  private readonly trendsLoading = this.store.selectSignal(selectTrendsLoading);

  // Combined loading — true until all three APIs respond
  protected readonly loading = computed(
    () => this.projectDetailLoading() || this.reportsLoading() || this.trendsLoading(),
  );

  // Combined view model built from store data
  protected readonly project = computed((): ProjectDetailView | undefined => {
    const dataset = this.datasetFromStore();
    if (!dataset) return undefined;

    const reports = this.allReports();
    const summary = this.reportsSummary();
    const trends = this.trendsData();

    const datasets: ReportAsDataset[] = reports.map((r) => ({
      id: r.id,
      projectId: dataset.id,
      name: r.datasetFileTitle || dataset.file_title || dataset.file_name,
      version: `v${r.datasetFileVersion}`,
      rows: r.fileRowsAnalyzed ?? 0,
      score: r.overallScore ?? 0,
      status: r.status,
      uploadedAt: r.generatedAt,
      activeRules: 0,
      failingRows: r.totalRowsFailed ?? 0,
    }));

    const scoreTrend: ScoreTrendPoint[] = trends.map((t) => ({
      version: t.snapshotDate,
      score: t.aggregatedScore,
    }));

    const avgScore = Math.round(summary?.averageScore ?? 0);

    return {
      id: dataset.id,
      name: dataset.file_title || dataset.file_name,
      datasetCount: summary?.totalActiveReports ?? 0,
      activeRulesCount: summary?.totalActiveRules ?? 0,
      lastRunAt: summary?.lastRuleCheckTime ?? dataset.updated_at,
      avgScore,
      status: avgScore >= 85 ? 'healthy' : avgScore >= 70 ? 'warning' : 'failing',
      datasets,
      scoreTrend,
    };
  });

  // Manage rules view — kept with MockDataService (rule management not in scope)
  protected readonly showManageRules = signal(false);
  protected readonly selectedDatasetId = signal<string>('');
  protected readonly validationRules = signal<ValidationRule[]>([]);
  protected readonly datasetColumns = signal<string[]>([]);

  // Add rule form state
  protected readonly newRuleType = signal('not_null');
  protected readonly newRuleColumn = signal('');
  protected readonly newRuleParams = signal('');

  // Edit rule state
  protected readonly editingRuleId = signal<string | null>(null);
  protected readonly editDraft = signal<EditDraft | null>(null);

  // Delete rule state
  protected readonly deleteTargetId = signal<string | null>(null);

  protected readonly selectedDataset = computed(() =>
    this.project()?.datasets.find((d) => d.id === this.selectedDatasetId()),
  );

  protected readonly activeRuleCount = computed(
    () => this.validationRules().filter((r) => r.enabled).length,
  );

  protected readonly deleteTargetRule = computed(() =>
    this.validationRules().find((r) => r.id === this.deleteTargetId()),
  );

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    // Clear stale state before loading new project
    this.store.dispatch(ProjectDetailActions.clearProjectDetail());
    this.store.dispatch(ReportsActions.clearReports());
    this.store.dispatch(TrendsActions.clearTrends());
    // Dispatch all three in parallel — effects run concurrently
    this.store.dispatch(ProjectDetailActions.loadProjectDetail({ datasetId: id }));
    this.store.dispatch(ReportsActions.loadReports({ datasetId: id }));
    this.store.dispatch(TrendsActions.loadTrends({ datasetId: id }));
  }

  ngOnDestroy(): void {
    this.store.dispatch(ProjectDetailActions.clearProjectDetail());
    this.store.dispatch(ReportsActions.clearReports());
    this.store.dispatch(TrendsActions.clearTrends());
  }

  protected openManageRules(): void {
    const firstDataset = this.project()?.datasets[0];
    if (firstDataset) {
      this.selectedDatasetId.set(firstDataset.id);
      this.loadDatasetData(firstDataset.id);
    }
    this.showManageRules.set(true);
  }

  protected selectDataset(id: string): void {
    this.cancelEdit();
    this.selectedDatasetId.set(id);
    this.loadDatasetData(id);
  }

  private loadDatasetData(id: string): void {
    this.dataService.getValidationRules(id).subscribe((rules) => this.validationRules.set(rules));
    this.dataService.getDatasetColumns(id).subscribe((cols) => {
      this.datasetColumns.set(cols);
      if (cols.length) this.newRuleColumn.set(cols[0]);
    });
  }

  // ── Toggle ──────────────────────────────────────────────────────────────────

  protected toggleRule(id: string): void {
    this.validationRules.update((rules) =>
      rules.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r)),
    );
  }

  // ── Edit ────────────────────────────────────────────────────────────────────

  protected startEdit(rule: ValidationRule): void {
    this.editingRuleId.set(rule.id);
    this.editDraft.set({
      name: rule.name,
      description: rule.description,
      type: rule.type,
      column: rule.column,
    });
  }

  protected patchDraft(key: keyof EditDraft, e: Event): void {
    const val = (e.target as HTMLInputElement | HTMLSelectElement).value;
    this.editDraft.update((d) => (d ? { ...d, [key]: val } : null));
  }

  protected saveEdit(): void {
    const id = this.editingRuleId();
    const draft = this.editDraft();
    if (!id || !draft) return;
    this.validationRules.update((rules) =>
      rules.map((r) => (r.id === id ? { ...r, ...draft } : r)),
    );
    this.editingRuleId.set(null);
    this.editDraft.set(null);
  }

  protected cancelEdit(): void {
    this.editingRuleId.set(null);
    this.editDraft.set(null);
  }

  // ── Delete ──────────────────────────────────────────────────────────────────

  protected requestDelete(id: string): void {
    this.deleteTargetId.set(id);
  }

  protected confirmDelete(): void {
    const id = this.deleteTargetId();
    if (id) this.validationRules.update((rules) => rules.filter((r) => r.id !== id));
    this.deleteTargetId.set(null);
  }

  protected cancelDelete(): void {
    this.deleteTargetId.set(null);
  }

  // ── Add ─────────────────────────────────────────────────────────────────────

  protected addRule(): void {
    const type = this.newRuleType() as ValidationRule['type'];
    const col = this.newRuleColumn();
    if (!col) return;
    const newRule: ValidationRule = {
      id: 'r' + Date.now(),
      name: `${type.replace('_', ' ')} on ${col}`,
      description: `${col} must pass ${type.replace('_', ' ')} check`,
      type,
      column: col,
      enabled: true,
      status: 'passing',
    };
    this.validationRules.update((rules) => [...rules, newRule]);
    this.newRuleParams.set('');
  }

  // ── Helpers ─────────────────────────────────────────────────────────────────

  protected scoreClass(score: number): string {
    if (score >= 85) return 'score--healthy';
    if (score >= 70) return 'score--warning';
    return 'score--failing';
  }

  protected statusVariant(status: string): 'success' | 'warning' | 'danger' {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      default:
        return 'danger';
    }
  }

  protected statusLabel(status: string): string {
    return status.charAt(0).toUpperCase() + status.slice(1);
  }

  protected relativeTime(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  }

  protected totalFailingRows(): number {
    return this.project()?.datasets.reduce((sum, d) => sum + d.failingRows, 0) ?? 0;
  }
}
