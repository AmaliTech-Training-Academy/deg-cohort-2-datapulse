import { Component, computed, inject, input } from '@angular/core';
import { Store } from '@ngrx/store';
import { ThemeService } from '../../../../core/services/theme.service';
import * as AuthActions from '../../../../features/auth/store/auth.actions';
import { User } from '../../../../features/auth/auth.models';

@Component({
  selector: 'app-topbar',
  standalone: true,
  templateUrl: './topbar.html',
  styleUrl: './topbar.css',
})
export class TopbarComponent {
  readonly user = input<User | null>(null);

  private readonly store = inject(Store);
  protected readonly themeService = inject(ThemeService);

  protected readonly initials = computed(() => {
    const u = this.user();
    if (!u) return '';
    return `${u.first_name} ${u.last_name}`
      .trim()
      .split(' ')
      .map((w) => w[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
  });

  protected readonly roleLabel = computed(() => {
    const u = this.user();
    if (!u) return '';
    return u.role === 'admin' ? 'Administrator' : 'Data Engineer';
  });

  protected toggleTheme(): void {
    this.themeService.toggle();
  }

  protected logout(): void {
    this.store.dispatch(AuthActions.logout());
  }
}
