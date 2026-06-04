import { Injectable, computed, signal } from '@angular/core';

type Theme = 'light' | 'dark' | 'system';

const THEME_KEY = 'datapulse_theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly theme = signal<Theme>(this.loadTheme());

  readonly isDark = computed(() => {
    const t = this.theme();
    if (t === 'dark') return true;
    if (t === 'light') return false;
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  init(): void {
    this.applyClass();
  }

  toggle(): void {
    const next: Theme = this.isDark() ? 'light' : 'dark';
    this.theme.set(next);
    localStorage.setItem(THEME_KEY, next);
    this.applyClass();
  }

  private applyClass(): void {
    const html = document.documentElement;
    html.classList.remove('dark', 'light');
    const t = this.theme();
    if (t !== 'system') {
      html.classList.add(t);
    }
  }

  private loadTheme(): Theme {
    return (localStorage.getItem(THEME_KEY) as Theme) ?? 'system';
  }
}
