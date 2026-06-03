import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-general-settings',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './general.html',
  styleUrl: './general.css',
})
export class GeneralSettingsComponent {
  protected orgName = 'Acme Corp';
  protected timezone = 'UTC';
}
