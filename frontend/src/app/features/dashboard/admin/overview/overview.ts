import { Component, computed, inject, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Store } from '@ngrx/store';
import { StatCardComponent } from '../../../../shared/ui/stat-card/stat-card';
import { BadgeComponent } from '../../../../shared/ui/badge/badge';
import { ProjectStatus } from '../../../../shared/models/dashboard.models';
import * as AdminProjectsActions from '../../store/admin-projects/admin-projects.actions';
import * as AdminUsersActions from '../../store/admin-users/admin-users.actions';
import {
  selectAdminDatasets,
  selectAdminProjectsLoading,
  selectAdminProjectsTotal,
} from '../../store/admin-projects/admin-projects.selectors';
import {
  selectAdminUsers,
  selectAdminUsersLoading,
  selectAdminUsersTotal,
} from '../../store/admin-users/admin-users.selectors';

@Component({
  selector: 'app-overview',
  standalone: true,
  imports: [RouterLink, StatCardComponent, BadgeComponent],
  templateUrl: './overview.html',
  styleUrl: './overview.css',
})
export class OverviewComponent implements OnInit {
  private readonly store = inject(Store);

  protected readonly datasets = this.store.selectSignal(selectAdminDatasets);
  protected readonly totalProjects = this.store.selectSignal(selectAdminProjectsTotal);
  protected readonly projectsLoading = this.store.selectSignal(selectAdminProjectsLoading);

  protected readonly users = this.store.selectSignal(selectAdminUsers);
  protected readonly totalUsers = this.store.selectSignal(selectAdminUsersTotal);
  protected readonly usersLoading = this.store.selectSignal(selectAdminUsersLoading);

  protected readonly loading = computed(
    () => this.projectsLoading() || this.usersLoading(),
  );

  protected readonly stats = computed(() => ({
    totalProjects: this.totalProjects(),
    failingDatasets: this.datasets().filter((d) => d.status === 'failing').length,
    activeUsers: this.users().filter((u) => u.isActive).length,
    adminCount: this.users().filter((u) => u.role === 'admin').length,
  }));

  protected readonly recentProjects = computed(() =>
    [...this.datasets()]
      .sort((a, b) => {
        const ta = a.lastRunAt ? new Date(a.lastRunAt).getTime() : 0;
        const tb = b.lastRunAt ? new Date(b.lastRunAt).getTime() : 0;
        return tb - ta;
      })
      .slice(0, 5),
  );

  protected readonly recentUsers = computed(() => this.users().slice(0, 5));

  ngOnInit(): void {
    this.store.dispatch(AdminProjectsActions.loadAdminProjects({}));
    this.store.dispatch(AdminUsersActions.loadAdminUsers());
  }

  protected scoreClass(score: number): string {
    if (score >= 85) return 'score--healthy';
    if (score >= 70) return 'score--warning';
    return 'score--failing';
  }

  protected statusLabel(status: ProjectStatus): string {
    return status.charAt(0).toUpperCase() + status.slice(1);
  }

  protected statusVariant(status: ProjectStatus): 'success' | 'warning' | 'danger' {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      default: return 'danger';
    }
  }

  protected roleBadge(role: string): 'info' | 'neutral' {
    return role === 'admin' ? 'info' : 'neutral';
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
}
