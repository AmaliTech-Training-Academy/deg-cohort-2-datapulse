import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { Store } from '@ngrx/store';
import { StatCardComponent } from '../../../../shared/ui/stat-card/stat-card';
import { BadgeComponent } from '../../../../shared/ui/badge/badge';
import { AdminUser } from '../../models/admin-user.model';
import * as AdminUsersActions from '../../store/admin-users/admin-users.actions';
import {
  selectAdminUsers,
  selectAdminUsersError,
  selectAdminUsersLoading,
  selectAdminUsersTotal,
} from '../../store/admin-users/admin-users.selectors';

type RoleFilter = 'all' | 'admin' | 'user';

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [StatCardComponent, BadgeComponent],
  templateUrl: './users.html',
  styleUrl: './users.css',
})
export class UsersComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);

  protected readonly allUsers = this.store.selectSignal(selectAdminUsers);
  protected readonly total = this.store.selectSignal(selectAdminUsersTotal);
  protected readonly loading = this.store.selectSignal(selectAdminUsersLoading);
  protected readonly error = this.store.selectSignal(selectAdminUsersError);

  protected readonly searchQuery = signal('');
  protected readonly roleFilter = signal<RoleFilter>('all');
  protected readonly currentPage = signal(1);
  protected readonly pageSize = 10;

  protected readonly stats = computed(() => {
    const users = this.allUsers();
    return {
      total: this.total(),
      admins: users.filter((u) => u.role === 'admin').length,
      active: users.filter((u) => u.isActive).length,
      unverified: users.filter((u) => !u.isEmailVerified).length,
    };
  });

  protected readonly filteredUsers = computed(() => {
    const q = this.searchQuery().toLowerCase();
    const role = this.roleFilter();
    let list: AdminUser[] = this.allUsers();

    if (role !== 'all') list = list.filter((u) => u.role === role);
    if (q)
      list = list.filter(
        (u) =>
          u.fullName.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q),
      );
    return list;
  });

  protected readonly totalPages = computed(() =>
    Math.max(1, Math.ceil(this.filteredUsers().length / this.pageSize)),
  );

  protected readonly pagedUsers = computed(() => {
    const page = this.currentPage();
    const start = (page - 1) * this.pageSize;
    return this.filteredUsers().slice(start, start + this.pageSize);
  });

  protected readonly pageInfo = computed(() => {
    const total = this.filteredUsers().length;
    const page = this.currentPage();
    const from = Math.min((page - 1) * this.pageSize + 1, total);
    const to = Math.min(page * this.pageSize, total);
    return { from, to, total };
  });

  ngOnInit(): void {
    this.store.dispatch(AdminUsersActions.loadAdminUsers());
  }

  ngOnDestroy(): void {
    this.store.dispatch(AdminUsersActions.clearAdminUsers());
  }

  protected setRoleFilter(role: RoleFilter): void {
    this.roleFilter.set(role);
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

  protected statusVariant(user: AdminUser): 'success' | 'warning' | 'neutral' {
    if (!user.isEmailVerified) return 'warning';
    return user.isActive ? 'success' : 'neutral';
  }

  protected statusLabel(user: AdminUser): string {
    if (!user.isEmailVerified) return 'Unverified';
    return user.isActive ? 'Active' : 'Inactive';
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
