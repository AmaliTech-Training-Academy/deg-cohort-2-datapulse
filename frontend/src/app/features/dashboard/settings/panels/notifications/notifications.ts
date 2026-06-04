import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-notifications-settings',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './notifications.html',
  styleUrl: './notifications.css',
})
export class NotificationsSettingsComponent {
  protected emailOnCritical = true;
  protected emailOnWarning = true;
  protected emailDigestDaily = false;
  protected slackWebhook = '';
}
