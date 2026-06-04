import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MockDataService } from '../../../../shared/services/mock-data.service';
import { Project, ProjectStatus } from '../../../../shared/models/dashboard.models';
import { StatCardComponent } from '../../../../shared/ui/stat-card/stat-card';
import { BadgeComponent } from '../../../../shared/ui/badge/badge';

type FilterTab = 'all' | ProjectStatus;

@Component({
  selector: 'app-all-projects',
  standalone: true,
  imports: [FormsModule, StatCardComponent, BadgeComponent],
  templateUrl: './all-projects.html',
  styleUrl: './all-projects.css',
})
export class AllProjectsComponent implements OnInit {
  private readonly dataService = inject(MockDataService);

  protected readonly allProjects = signal<Project[]>([]);
  protected readonly searchQuery = signal('');
  protected readonly activeFilter = signal<FilterTab>('all');

  protected readonly stats = computed(() => ({
    total: 42,
    healthy: 31,
    warning: 6,
    failing: 5,
  }));

  protected readonly filteredProjects = computed(() => {
    const q = this.searchQuery().toLowerCase();
    let list = this.allProjects();
    const f = this.activeFilter();
    if (f !== 'all') list = list.filter((p) => p.status === f);
    if (q) list = list.filter((p) => p.name.toLowerCase().includes(q) || p.ownerName.toLowerCase().includes(q));
    return list;
  });

  protected readonly tabCounts = computed(() => ({
    all: this.allProjects().length,
    healthy: this.allProjects().filter((p) => p.status === 'healthy').length,
    warning: this.allProjects().filter((p) => p.status === 'warning').length,
    failing: this.allProjects().filter((p) => p.status === 'failing').length,
  }));

  ngOnInit(): void {
    this.dataService.getAllProjects().subscribe((p) => this.allProjects.set(p));
  }

  protected setFilter(f: FilterTab): void {
    this.activeFilter.set(f);
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
      case 'failing': return 'danger';
    }
  }

  protected statusLabel(status: ProjectStatus): string {
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

  protected onSearch(event: Event): void {
    this.searchQuery.set((event.target as HTMLInputElement).value);
  }
}
