import { Component, inject, OnInit } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { Store } from '@ngrx/store';
import { BadgeComponent } from '../../../../shared/ui/badge/badge';
import * as ProjectsActions from '../../store/projects/projects.actions';
import {
  selectAllProjects,
  selectProjectsError,
  selectProjectsLoading,
} from '../../store/projects/projects.selectors';

@Component({
  selector: 'app-my-projects',
  standalone: true,
  imports: [RouterLink, BadgeComponent],
  templateUrl: './projects.html',
  styleUrl: './projects.css',
})
export class MyProjectsComponent implements OnInit {
  private readonly store = inject(Store);
  private readonly router = inject(Router);

  protected readonly projects = this.store.selectSignal(selectAllProjects);
  protected readonly loading = this.store.selectSignal(selectProjectsLoading);
  protected readonly error = this.store.selectSignal(selectProjectsError);

  ngOnInit(): void {
    this.store.dispatch(ProjectsActions.loadProjects());
  }

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

  protected iconPath(iconKey: string): string {
    const icons: Record<string, string> = {
      users: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
      'trending-up': 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
      bell: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9',
      database:
        'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4',
      layers: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
      mail: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
      grid: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z',
      activity: 'M22 12h-4l-3 9L9 3l-3 9H2',
    };
    return icons[iconKey] ?? icons['database'];
  }

  protected iconBg(iconKey: string): string {
    const colors: Record<string, string> = {
      users: '#eff6ff',
      'trending-up': '#f0fdf4',
      bell: '#fff7ed',
      database: '#fef2f2',
      layers: '#eff6ff',
      mail: '#fef9c3',
      grid: '#f5f3ff',
      activity: '#fef2f2',
    };
    return colors[iconKey] ?? '#f3f4f6';
  }

  protected iconColor(iconKey: string): string {
    const colors: Record<string, string> = {
      users: '#2563eb',
      'trending-up': '#16a34a',
      bell: '#ea580c',
      database: '#dc2626',
      layers: '#2563eb',
      mail: '#ca8a04',
      grid: '#7c3aed',
      activity: '#dc2626',
    };
    return colors[iconKey] ?? '#6b7280';
  }

  protected navigateToProject(id: string): void {
    this.router.navigate(['/dashboard/projects', id]);
  }
}
