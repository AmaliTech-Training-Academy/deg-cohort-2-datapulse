import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { MockDataService } from '../../../shared/services/mock-data.service';
import { Alert, AlertSeverity } from '../../../shared/models/dashboard.models';
import { StatCardComponent } from '../../../shared/ui/stat-card/stat-card';

type AlertFilter = 'all' | 'unread' | 'resolved';

@Component({
  selector: 'app-alerts',
  standalone: true,
  imports: [StatCardComponent],
  templateUrl: './alerts.html',
  styleUrl: './alerts.css',
})
export class AlertsComponent implements OnInit {
  private readonly dataService = inject(MockDataService);

  protected readonly alerts = signal<Alert[]>([]);
  protected readonly activeFilter = signal<AlertFilter>('all');

  protected readonly stats = computed(() => {
    const a = this.alerts();
    return {
      critical: a.filter((x) => x.severity === 'critical').length,
      warnings: a.filter((x) => x.severity === 'warning' || x.severity === 'slow' || x.severity === 'breach').length,
      unread: a.filter((x) => !x.isRead).length,
      resolved: a.filter((x) => x.isResolved).length,
    };
  });

  protected readonly filtered = computed(() => {
    const f = this.activeFilter();
    const a = this.alerts();
    if (f === 'unread') return a.filter((x) => !x.isRead);
    if (f === 'resolved') return a.filter((x) => x.isResolved);
    return a;
  });

  protected readonly tabCounts = computed(() => ({
    all: this.alerts().length,
    unread: this.alerts().filter((x) => !x.isRead).length,
    resolved: this.alerts().filter((x) => x.isResolved).length,
  }));

  ngOnInit(): void {
    this.dataService.getAlerts().subscribe((a) => this.alerts.set(a));
  }

  protected setFilter(f: AlertFilter): void {
    this.activeFilter.set(f);
  }

  protected markAllRead(): void {
    this.alerts.update((a) => a.map((x) => ({ ...x, isRead: true })));
  }

  protected severityIcon(s: AlertSeverity): string {
    switch (s) {
      case 'critical':
        return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z';
      case 'warning':
        return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z';
      case 'slow':
        return 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z';
      case 'breach':
        return 'M13 10V3L4 14h7v7l9-11h-7z';
      case 'resolved':
        return 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z';
    }
  }

  protected severityColor(s: AlertSeverity): string {
    switch (s) {
      case 'critical': return 'var(--color-danger)';
      case 'warning': return 'var(--color-warning)';
      case 'slow': return 'var(--color-warning)';
      case 'breach': return 'var(--color-danger)';
      case 'resolved': return 'var(--color-success)';
    }
  }

  protected relativeTime(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  }
}
