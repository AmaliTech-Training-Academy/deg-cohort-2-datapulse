import { Component, computed, effect, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Store } from '@ngrx/store';
import { Actions, ofType } from '@ngrx/effects';
import { ValidationRule, ScoreTrendPoint } from '../../../../shared/models/dashboard.models';
import { selectUserRole } from '../../../../features/auth/store/auth.selectors';
import { StatCardComponent } from '../../../../shared/ui/stat-card/stat-card';
import { BadgeComponent } from '../../../../shared/ui/badge/badge';
import { TrendChartComponent } from '../../../../shared/ui/trend-chart/trend-chart';
import { ConfirmationModalComponent } from '../../../../shared/ui/confirmation-modal/confirmation-modal';
import { StepErrorComponent } from '../../../../shared/ui/step-error/step-error';
import * as ProjectDetailActions from '../../store/project-detail/project-detail.actions';
import * as ReportsActions from '../../store/reports/reports.actions';
import * as TrendsActions from '../../store/trends/trends.actions';
import * as ValidationRulesActions from '../../store/validation-rules/validation-rules.actions';
import {
  selectProjectDetailDataset,
  selectProjectDetailLoading,
  selectUploadVersionError,
  selectUploadVersionLoading,
} from '../../store/project-detail/project-detail.selectors';
import {
  selectAllReports,
  selectReportsLoading,
  selectReportsSummary,
} from '../../store/reports/reports.selectors';
import { selectTrendsData, selectTrendsLoading } from '../../store/trends/trends.selectors';
import {
  selectAddRuleError,
  selectAddRuleLoading,
  selectAllRules,
  selectDeleteError,
  selectDeleteLoadingId,
  selectHasChanges,
  selectRunCheckError,
  selectRunCheckLoading,
  selectRulesLoading,
} from '../../store/validation-rules/validation-rules.selectors';
import { ProjectStatus } from '../../models/project.model';
import {
  buildRuleConfig,
  mapFrontendTypeToApi,
} from '../../models/validation-rule.model';

interface EditDraft {
  name: string;
  description: string;
  type: ValidationRule['type'];
  column: string;
}

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
  passingRows: number;
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
  imports: [
    RouterLink,
    StatCardComponent,
    BadgeComponent,
    TrendChartComponent,
    ConfirmationModalComponent,
    StepErrorComponent,
  ],
  templateUrl: './project-detail.html',
  styleUrl: './project-detail.css',
})
export class ProjectDetailComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly store = inject(Store);
  private readonly actions$ = inject(Actions);

  protected readonly role = this.store.selectSignal(selectUserRole);
  protected readonly projectsLink = () =>
    this.role() === 'admin' ? '/dashboard/all-projects' : '/dashboard/projects';

  // Project detail store signals
  private readonly datasetFromStore = this.store.selectSignal(selectProjectDetailDataset);
  private readonly projectDetailLoading = this.store.selectSignal(selectProjectDetailLoading);
  private readonly allReports = this.store.selectSignal(selectAllReports);
  private readonly reportsSummary = this.store.selectSignal(selectReportsSummary);
  private readonly trendsData = this.store.selectSignal(selectTrendsData);
  private readonly reportsLoading = this.store.selectSignal(selectReportsLoading);
  private readonly trendsLoading = this.store.selectSignal(selectTrendsLoading);

  protected readonly loading = computed(
    () => this.projectDetailLoading() || this.reportsLoading() || this.trendsLoading(),
  );

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
      passingRows: r.totalRowsPassed ?? 0,
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

  // Validation rules store signals
  private readonly storeRules = this.store.selectSignal(selectAllRules);
  protected readonly rulesLoading = this.store.selectSignal(selectRulesLoading);
  protected readonly addRuleLoading = this.store.selectSignal(selectAddRuleLoading);
  protected readonly addRuleError = this.store.selectSignal(selectAddRuleError);
  protected readonly deleteLoadingId = this.store.selectSignal(selectDeleteLoadingId);
  protected readonly deleteError = this.store.selectSignal(selectDeleteError);
  protected readonly runCheckLoading = this.store.selectSignal(selectRunCheckLoading);
  protected readonly runCheckError = this.store.selectSignal(selectRunCheckError);
  protected readonly hasChanges = this.store.selectSignal(selectHasChanges);

  // Local overlays applied on top of store rules (toggle/edit don't persist to backend)
  private readonly localToggledOff = signal(new Set<string>());
  private readonly localEdits = signal(new Map<string, Partial<ValidationRule>>());

  protected readonly validationRules = computed(() => {
    const toggled = this.localToggledOff();
    const edits = this.localEdits();
    return this.storeRules().map((r) => ({
      ...r,
      ...(edits.get(r.id) ?? {}),
      enabled: !toggled.has(r.id),
    }));
  });

  // Upload version store signals
  protected readonly uploadVersionLoading = this.store.selectSignal(selectUploadVersionLoading);
  protected readonly uploadVersionError = this.store.selectSignal(selectUploadVersionError);

  // Upload version modal state
  protected readonly showUploadModal = signal(false);
  protected readonly uploadFileName = signal<string | null>(null);
  protected readonly uploadIsDragOver = signal(false);
  protected readonly uploadParseError = signal<string | null>(null);
  private pendingVersionFile: File | null = null;

  // Manage rules UI state
  protected readonly showManageRules = signal(false);
  protected readonly selectedDatasetId = signal<string>('');

  // Add rule form
  protected readonly newRuleType = signal('not_null');
  protected readonly newRuleColumn = signal('');
  protected readonly newRuleParams = signal('');

  // Edit rule state
  protected readonly editingRuleId = signal<string | null>(null);
  protected readonly editDraft = signal<EditDraft | null>(null);

  // Delete rule state
  protected readonly deleteTargetId = signal<string | null>(null);

  // Derived from store dataset
  protected readonly datasetColumns = computed(() => this.datasetFromStore()?.columns ?? []);

  protected readonly selectedDataset = computed(() =>
    this.project()?.datasets.find((d) => d.id === this.selectedDatasetId()),
  );

  protected readonly activeRuleCount = computed(
    () => this.validationRules().filter((r) => r.enabled).length,
  );

  protected readonly deleteTargetRule = computed(() =>
    this.validationRules().find((r) => r.id === this.deleteTargetId()),
  );

  constructor() {
    // Reset local overlays whenever the canonical rule list reloads
    effect(() => {
      this.storeRules();
      this.localToggledOff.set(new Set());
      this.localEdits.set(new Map());
    });

    // Pre-select first column for the add-rule form once columns are available
    effect(() => {
      const cols = this.datasetColumns();
      if (cols.length && !this.newRuleColumn()) {
        this.newRuleColumn.set(cols[0]);
      }
    });

    // Close manage-rules panel and return to project-detail view after run-check completes
    this.actions$
      .pipe(ofType(ValidationRulesActions.runChecksOnDatasetSuccess), takeUntilDestroyed())
      .subscribe(() => this.showManageRules.set(false));

    // Close upload modal — the effect handles dispatching the three reload actions
    this.actions$
      .pipe(ofType(ProjectDetailActions.uploadVersionSuccess), takeUntilDestroyed())
      .subscribe(() => {
        this.showUploadModal.set(false);
        this.uploadFileName.set(null);
        this.pendingVersionFile = null;
      });
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.store.dispatch(ProjectDetailActions.clearProjectDetail());
    this.store.dispatch(ReportsActions.clearReports());
    this.store.dispatch(TrendsActions.clearTrends());
    this.store.dispatch(ValidationRulesActions.clearValidationRules());
    this.store.dispatch(ProjectDetailActions.loadProjectDetail({ datasetId: id }));
    this.store.dispatch(ReportsActions.loadReports({ datasetId: id }));
    this.store.dispatch(TrendsActions.loadTrends({ datasetId: id }));
  }

  ngOnDestroy(): void {
    this.store.dispatch(ProjectDetailActions.clearProjectDetail());
    this.store.dispatch(ReportsActions.clearReports());
    this.store.dispatch(TrendsActions.clearTrends());
    this.store.dispatch(ValidationRulesActions.clearValidationRules());
  }

  // ── Upload version modal ─────────────────────────────────────────────────────

  protected openUploadModal(): void {
    this.uploadFileName.set(null);
    this.uploadParseError.set(null);
    this.pendingVersionFile = null;
    this.showUploadModal.set(true);
  }

  protected closeUploadModal(): void {
    this.showUploadModal.set(false);
  }

  protected onUploadDragOver(event: DragEvent): void {
    event.preventDefault();
    this.uploadIsDragOver.set(true);
  }

  protected onUploadDragLeave(): void {
    this.uploadIsDragOver.set(false);
  }

  protected onUploadDrop(event: DragEvent): void {
    event.preventDefault();
    this.uploadIsDragOver.set(false);
    const file = event.dataTransfer?.files[0];
    if (file) this.setVersionFile(file);
  }

  protected onUploadFileSelect(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) this.setVersionFile(file);
  }

  private setVersionFile(file: File): void {
    const lower = file.name.toLowerCase();
    if (!lower.endsWith('.csv') && !lower.endsWith('.json')) {
      this.uploadParseError.set('Only .csv and .json files are supported.');
      return;
    }
    this.uploadParseError.set(null);
    this.pendingVersionFile = file;
    this.uploadFileName.set(file.name);
  }

  protected submitUploadVersion(): void {
    const datasetId = this.datasetFromStore()?.id;
    if (!this.pendingVersionFile || !datasetId) return;
    this.store.dispatch(
      ProjectDetailActions.uploadVersion({ datasetId, file: this.pendingVersionFile }),
    );
  }

  protected openManageRules(): void {
    const datasetId = this.datasetFromStore()?.id;
    if (datasetId) {
      this.store.dispatch(ValidationRulesActions.loadRules({ datasetId }));
    }
    const firstDataset = this.project()?.datasets[0];
    if (firstDataset) {
      this.selectedDatasetId.set(firstDataset.id);
    }
    this.showManageRules.set(true);
  }

  protected selectDataset(id: string): void {
    this.cancelEdit();
    this.selectedDatasetId.set(id);
    // rules are dataset-level (not per-report), no reload needed
  }

  // ── Toggle (local only, does not persist to backend) ────────────────────────

  protected toggleRule(id: string): void {
    this.localToggledOff.update((set) => {
      const next = new Set(set);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  // ── Edit (local only, does not persist to backend) ──────────────────────────

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
    this.localEdits.update((map) => {
      const next = new Map(map);
      next.set(id, draft);
      return next;
    });
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
    if (id) {
      this.store.dispatch(ValidationRulesActions.deleteRule({ ruleId: id }));
    }
    this.deleteTargetId.set(null);
  }

  protected cancelDelete(): void {
    this.deleteTargetId.set(null);
  }

  // ── Add ─────────────────────────────────────────────────────────────────────

  protected addRule(): void {
    const col = this.newRuleColumn();
    const datasetId = this.datasetFromStore()?.id;
    if (!col || !datasetId) return;

    const type = this.newRuleType();
    const params = this.newRuleParams();

    this.store.dispatch(
      ValidationRulesActions.addRule({
        datasetId,
        request: {
          column_name: col,
          rule_type: mapFrontendTypeToApi(type),
          rule_config: buildRuleConfig(type, params),
        },
      }),
    );
    this.newRuleParams.set('');
  }

  // ── Re-run checks ────────────────────────────────────────────────────────────

  protected reRunChecks(): void {
    const datasetId = this.datasetFromStore()?.id;
    if (datasetId) {
      this.store.dispatch(ValidationRulesActions.runChecksOnDataset({ datasetId }));
    }
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
