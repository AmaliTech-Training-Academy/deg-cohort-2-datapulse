import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { StatCardComponent } from '../../../../shared/ui/stat-card/stat-card';
import { BadgeComponent } from '../../../../shared/ui/badge/badge';
import { AdminDataset } from '../../models/admin-dataset.model';
import { ProjectStatus } from '../../../../shared/models/dashboard.models';
import * as AdminProjectsActions from '../../store/admin-projects/admin-projects.actions';
import {
  selectAdminDatasets,
  selectAdminProjectsError,
  selectAdminProjectsLoading,
  selectAdminProjectsTotal,
} from '../../store/admin-projects/admin-projects.selectors';

type FilterTab = 'all' | ProjectStatus;
type FileTypeFilter = 'all' | 'csv' | 'json';

@Component({
  selector: 'app-all-projects',
  standalone: true,
  imports: [FormsModule, StatCardComponent, BadgeComponent],
  templateUrl: './all-projects.html',
  styleUrl: './all-projects.css',
})
export class AllProjectsComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly router = inject(Router);

  protected readonly allDatasets = this.store.selectSignal(selectAdminDatasets);
  protected readonly total = this.store.selectSignal(selectAdminProjectsTotal);
  protected readonly loading = this.store.selectSignal(selectAdminProjectsLoading);
  protected readonly error = this.store.selectSignal(selectAdminProjectsError);

  protected readonly searchQuery = signal('');
  protected readonly activeFilter = signal<FilterTab>('all');
  protected readonly fileTypeFilter = signal<FileTypeFilter>('all');
  protected readonly currentPage = signal(1);
  protected readonly pageSize = 10;

  protected readonly stats = computed(() => {
    const ds = this.allDatasets();
    return {
      total: this.total(),
      healthy: ds.filter((d) => d.status === 'healthy').length,
      warning: ds.filter((d) => d.status === 'warning').length,
      failing: ds.filter((d) => d.status === 'failing').length,
    };
  });

  protected readonly filteredProjects = computed(() => {
    const q = this.searchQuery().toLowerCase();
    const status = this.activeFilter();
    const ft = this.fileTypeFilter();
    let list: AdminDataset[] = this.allDatasets();

    if (status !== 'all') list = list.filter((d) => d.status === status);
    if (ft !== 'all') list = list.filter((d) => d.fileType === ft);
    if (q)
      list = list.filter(
        (d) =>
          d.name.toLowerCase().includes(q) ||
          d.ownerName.toLowerCase().includes(q) ||
          d.ownerEmail.toLowerCase().includes(q),
      );
    return list;
  });

  protected readonly totalPages = computed(() =>
    Math.max(1, Math.ceil(this.filteredProjects().length / this.pageSize)),
  );

  protected readonly pagedProjects = computed(() => {
    const page = this.currentPage();
    const start = (page - 1) * this.pageSize;
    return this.filteredProjects().slice(start, start + this.pageSize);
  });

  protected readonly pageInfo = computed(() => {
    const total = this.filteredProjects().length;
    const page = this.currentPage();
    const from = Math.min((page - 1) * this.pageSize + 1, total);
    const to = Math.min(page * this.pageSize, total);
    return { from, to, total };
  });

  protected readonly tabCounts = computed(() => {
    const ds = this.allDatasets();
    return {
      all: ds.length,
      healthy: ds.filter((d) => d.status === 'healthy').length,
      warning: ds.filter((d) => d.status === 'warning').length,
      failing: ds.filter((d) => d.status === 'failing').length,
    };
  });

  ngOnInit(): void {
    this.store.dispatch(AdminProjectsActions.loadAdminProjects({}));
  }

  ngOnDestroy(): void {
    this.store.dispatch(AdminProjectsActions.clearAdminProjects());
  }

  protected setFilter(f: FilterTab): void {
    this.activeFilter.set(f);
    this.currentPage.set(1);
  }

  protected setFileType(ft: FileTypeFilter): void {
    this.fileTypeFilter.set(ft);
    this.currentPage.set(1);
  }

  protected onSearch(event: Event): void {
    this.searchQuery.set((event.target as HTMLInputElement).value);
    this.currentPage.set(1);
  }

  protected prevPage(): void {
    this.currentPage.update((p) => Math.max(1, p - 1));
  }

  protected nextPage(): void {
    this.currentPage.update((p) => Math.min(this.totalPages(), p + 1));
  }

  protected goToPage(page: number): void {
    this.currentPage.set(page);
  }

  protected pageNumbers(): number[] {
    const total = this.totalPages();
    const current = this.currentPage();
    const delta = 2;
    const range: number[] = [];
    for (
      let i = Math.max(1, current - delta);
      i <= Math.min(total, current + delta);
      i++
    ) {
      range.push(i);
    }
    return range;
  }

  protected scoreClass(score: number): string {
    if (score >= 85) return 'score--healthy';
    if (score >= 70) return 'score--warning';
    return 'score--failing';
  }

  protected statusVariant(status: ProjectStatus): 'success' | 'warning' | 'danger' {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      default: return 'danger';
    }
  }

  protected statusLabel(status: ProjectStatus): string {
    return status.charAt(0).toUpperCase() + status.slice(1);
  }

  protected relativeTime(iso: string | null): string {
    if (!iso) return '—';
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  }

  protected goToProject(id: string): void {
    this.router.navigate(['/dashboard/projects', id]);
  }
}
