import { Component, input } from '@angular/core';

@Component({
  selector: 'app-auth-layout',
  standalone: true,
  templateUrl: './auth-layout.html',
  styleUrl: './auth-layout.css',
})
export class AuthLayoutComponent {
  readonly subtitle = input<string>('');
}
