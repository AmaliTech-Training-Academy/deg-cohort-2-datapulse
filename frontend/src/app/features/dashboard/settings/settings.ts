import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

interface SettingsNav {
  label: string;
  route: string;
}

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './settings.html',
  styleUrl: './settings.css',
})
export class SettingsComponent {
  protected readonly navItems: SettingsNav[] = [
    { label: 'Profile', route: 'profile' },
    { label: 'Danger zone', route: 'danger-zone' },
  ];
}
