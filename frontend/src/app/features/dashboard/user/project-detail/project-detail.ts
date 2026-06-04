import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MockDataService } from '../../../../shared/services/mock-data.service';
import { Project } from '../../../../shared/models/dashboard.models';
import { StatCardComponent } from '../../../../shared/ui/stat-card/stat-card';
import { BadgeComponent } from '../../../../shared/ui/badge/badge';
import { TrendChartComponent } from '../../../../shared/ui/trend-chart/trend-chart';

@Component({
  selector: 'app-project-detail',
  standalone: true,
  imports: [RouterLink, StatCardComponent, BadgeComponent, TrendChartComponent],
  templateUrl: './project-detail.html',
  styleUrl: './project-detail.css',
})
export class ProjectDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly dataService = inject(MockDataService);

  protected readonly project = signal<Project | undefined>(undefined);
  protected readonly loading = signal(true);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.dataService.getProjectById(id).subscribe((p) => {
      this.project.set(p);
      this.loading.set(false);
    });
  }

  protected scoreClass(score: number): string {
    if (score >= 85) return 'score--healthy';
    if (score >= 70) return 'score--warning';
    return 'score--failing';
  }

  protected statusVariant(status: string): 'success' | 'warning' | 'danger' {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      default: return 'danger';
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
