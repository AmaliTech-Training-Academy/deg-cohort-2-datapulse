import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Store } from '@ngrx/store';
import { SidebarComponent } from './components/sidebar/sidebar';
import { TopbarComponent } from './components/topbar/topbar';
import { selectUser } from '../auth/store/auth.selectors';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterOutlet, SidebarComponent, TopbarComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class DashboardComponent {
  private readonly store = inject(Store);
  protected readonly user = this.store.selectSignal(selectUser);
}
