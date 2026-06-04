import { Component, computed, inject } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectUser } from '../../../../../features/auth/store/auth.selectors';

@Component({
  selector: 'app-profile-settings',
  standalone: true,
  templateUrl: './profile.html',
  styleUrl: './profile.css',
})
export class ProfileSettingsComponent {
  private readonly store = inject(Store);

  protected readonly user = this.store.selectSignal(selectUser);

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

  protected readonly fullName = computed(() => {
    const u = this.user();
    if (!u) return '';
    return `${u.first_name} ${u.last_name}`.trim();
  });

  protected readonly roleLabel = computed(() => {
    const u = this.user();
    if (!u) return '';
    return u.role === 'admin' ? 'Administrator' : 'Member';
  });

  protected readonly memberSince = computed(() => {
    const u = this.user();
    if (!u?.created_at) return '';
    return new Date(u.created_at).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  });
}
