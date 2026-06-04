import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MockDataService } from '../../../../shared/services/mock-data.service';
import { Project, AdminUserRow } from '../../../../shared/models/dashboard.models';
import { StatCardComponent } from '../../../../shared/ui/stat-card/stat-card';
import { BadgeComponent } from '../../../../shared/ui/badge/badge';

interface PlatformStats {
  totalProjects: number;
  projectDelta: number;
  activeUsers: number;
  adminCount: number;
  checksToday: number;
  checksDatasetsCount: number;
  failingDatasets: number;
}

@Component({
  selector: 'app-overview',
  standalone: true,
  imports: [RouterLink, StatCardComponent, BadgeComponent],
  templateUrl: './overview.html',
  styleUrl: './overview.css',
})
export class OverviewComponent implements OnInit {
  private readonly dataService = inject(MockDataService);

  protected readonly stats = signal<PlatformStats | null>(null);
  protected readonly recentProjects = signal<Project[]>([]);
  protected readonly recentUsers = signal<AdminUserRow[]>([]);

  ngOnInit(): void {
    this.dataService.getPlatformStats().subscribe((s) => this.stats.set(s as PlatformStats));
    this.dataService.getAllProjects().subscribe((projects) =>
      this.recentProjects.set(
        [...projects].sort((a, b) => new Date(b.lastRunAt).getTime() - new Date(a.lastRunAt).getTime()).slice(0, 5),
      ),
    );
    this.dataService.getAllUsers().subscribe((users) => this.recentUsers.set(users.slice(0, 5)));
  }

  protected scoreClass(score: number): string {
    if (score >= 85) return 'score--healthy';
    if (score >= 70) return 'score--warning';
    return 'score--failing';
  }

  protected statusLabel(status: string): string {
    return status.charAt(0).toUpperCase() + status.slice(1);
  }

  protected statusVariant(status: string): 'success' | 'warning' | 'danger' {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      default: return 'danger';
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
