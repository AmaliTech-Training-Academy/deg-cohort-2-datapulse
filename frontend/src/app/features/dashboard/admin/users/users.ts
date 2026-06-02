import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { MockDataService } from '../../../../shared/services/mock-data.service';
import { AdminUserRow } from '../../../../shared/models/dashboard.models';
import { StatCardComponent } from '../../../../shared/ui/stat-card/stat-card';
import { BadgeComponent } from '../../../../shared/ui/badge/badge';

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [StatCardComponent, BadgeComponent],
  templateUrl: './users.html',
  styleUrl: './users.css',
})
export class UsersComponent implements OnInit {
  private readonly dataService = inject(MockDataService);

  protected readonly allUsers = signal<AdminUserRow[]>([]);
  protected readonly searchQuery = signal('');

  protected readonly filteredUsers = computed(() => {
    const q = this.searchQuery().toLowerCase();
    if (!q) return this.allUsers();
    return this.allUsers().filter(
      (u) => u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q),
    );
  });

  protected readonly stats = computed(() => ({
    total: 128,
    admins: 14,
    active: 119,
    pendingInvites: 6,
  }));

  ngOnInit(): void {
    this.dataService.getAllUsers().subscribe((u) => this.allUsers.set(u));
  }

  protected userInitials(name: string): string {
    return name
      .split(' ')
      .map((w) => w[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
  }

  protected roleBadge(role: string): 'info' | 'neutral' {
    return role === 'admin' ? 'info' : 'neutral';
  }

  protected statusBadge(status: string): 'success' | 'warning' | 'danger' | 'neutral' {
    switch (status) {
      case 'active': return 'success';
      case 'invited': return 'warning';
      case 'suspended': return 'danger';
      default: return 'neutral';
    }
  }

  protected statusLabel(status: string): string {
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

  protected onSearch(event: Event): void {
    this.searchQuery.set((event.target as HTMLInputElement).value);
  }
}
