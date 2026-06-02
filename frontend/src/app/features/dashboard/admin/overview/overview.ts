import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MockDataService } from '../../../../shared/services/mock-data.service';
import { Alert, AdminUserRow } from '../../../../shared/models/dashboard.models';
import { StatCardComponent } from '../../../../shared/ui/stat-card/stat-card';
import { BadgeComponent } from '../../../../shared/ui/badge/badge';
import { ProgressBarComponent } from '../../../../shared/ui/progress-bar/progress-bar';

interface PlatformStats {
  totalProjects: number;
  projectDelta: number;
  activeUsers: number;
  adminCount: number;
  checksToday: number;
  checksDatasetsCount: number;
  failingDatasets: number;
  storageUsedPercent: number;
  storageUsedTB: number;
  storageTotalTB: number;
  rulesRunToday: number;
  rulesTotalToday: number;
  rulesRunPercent: number;
  errorRate: number;
}

@Component({
  selector: 'app-overview',
  standalone: true,
  imports: [RouterLink, StatCardComponent, BadgeComponent, ProgressBarComponent],
  templateUrl: './overview.html',
  styleUrl: './overview.css',
})
export class OverviewComponent implements OnInit {
  private readonly dataService = inject(MockDataService);

  protected readonly stats = signal<PlatformStats | null>(null);
  protected readonly activeAlerts = signal<Alert[]>([]);
  protected readonly recentUsers = signal<AdminUserRow[]>([]);

  ngOnInit(): void {
    this.dataService.getPlatformStats().subscribe((s) => this.stats.set(s as PlatformStats));
    this.dataService.getAlerts().subscribe((alerts) =>
      this.activeAlerts.set(alerts.filter((a) => !a.isResolved).slice(0, 3)),
    );
    this.dataService.getAllUsers().subscribe((users) => this.recentUsers.set(users.slice(0, 5)));
  }

  protected severityIcon(severity: string): string {
    switch (severity) {
      case 'critical':
        return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z';
      case 'warning':
        return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z';
      case 'slow':
        return 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z';
      default:
        return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
    }
  }

  protected severityColor(severity: string): string {
    switch (severity) {
      case 'critical':
        return 'var(--color-danger)';
      case 'warning':
        return 'var(--color-warning)';
      case 'slow':
        return 'var(--color-warning)';
      default:
        return 'var(--color-text-muted)';
    }
  }

  protected userRoleBadge(role: string): 'info' | 'neutral' {
    return role === 'admin' ? 'info' : 'neutral';
  }

  protected userStatusBadge(status: string): 'success' | 'warning' | 'neutral' {
    switch (status) {
      case 'active': return 'success';
      case 'invited': return 'warning';
      default: return 'neutral';
    }
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
